"""Platform state and the production API.

Infer resolves the tenant from the token, then loads only that tenant's prod adapter and store.
Logs and metrics record hashes and counts, never request or record text.
"""
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

from .registry import Registry
from .store import KeyRing, TenantStore, offboard
from .tenancy import AccessDenied, AuthError, TenantContext, verify_token
from .trainers.tiny import load_model, predict


def tenant_hash(tenant_id: str, salt: bytes) -> str:
    return hmac.new(salt, tenant_id.encode(), hashlib.sha256).hexdigest()[:16]


@dataclass
class Platform:
    root: Path
    base_path: Path
    keyring: KeyRing = field(default_factory=KeyRing)
    audit: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=lambda: {"requests": 0, "denied": 0})
    retired: set[str] = field(default_factory=set)
    log_salt: bytes = field(default_factory=lambda: secrets.token_bytes(32))

    def __post_init__(self):
        self.root = Path(self.root)
        self.registry = Registry(self.root)
        self._models: dict[tuple[str, str], object] = {}

    def add_tenant(self, tenant_id: str) -> TenantStore:
        if tenant_id in self.retired:
            raise ValueError("offboarded tenant ids are never reused")
        store = self.store(tenant_id)
        self.keyring.create(tenant_id)
        return store

    def offboard(self, tenant_id: str) -> None:
        """Delete tenant data and key, drop loaded models, and refuse its tokens from now on."""
        offboard(self.root, tenant_id, self.keyring)
        self._models = {key: model for key, model in self._models.items() if key[0] != tenant_id}
        self.retired.add(tenant_id)

    def store(self, tenant_id: str) -> TenantStore:
        return TenantStore(self.root, tenant_id, self.keyring)

    def search(self, ctx: TenantContext, query: str) -> list[dict]:
        return self.store(ctx.tenant_id).search(ctx, query)

    def model_for(self, ctx: TenantContext):
        version = self.registry.prod_version(ctx, ctx.tenant_id)
        # The key includes the tenant, so two tenants can never share a loaded adapter.
        key = (ctx.tenant_id, version or "base")
        if key not in self._models:
            adapter = self.registry.adapter_path(ctx, ctx.tenant_id, version) if version else None
            self._models[key] = load_model(self.base_path, adapter)
        return self._models[key], version or "base"

    def log(self, event: str, tenant_id: str, **fields) -> None:
        self.audit.append({"event": event, "tenant": tenant_hash(tenant_id, self.log_salt), "time": time.time(), **fields})


class InferRequest(BaseModel):
    text: str
    tenant_id: str | None = None


class BreakGlassRequest(BaseModel):
    tenant_id: str
    reason: str


def create_app(platform: Platform, secret: bytes) -> FastAPI:
    app = FastAPI(title="Social 360 POC")

    def context(authorization: str = Header(default="")) -> TenantContext:
        platform.metrics["requests"] += 1
        try:
            ctx = verify_token(authorization.removeprefix("Bearer "), secret)
        except AuthError as exc:
            platform.metrics["denied"] += 1
            raise HTTPException(401, "invalid token") from exc
        if ctx.tenant_id in platform.retired:
            platform.metrics["denied"] += 1
            raise HTTPException(401, "tenant offboarded")
        return ctx

    def deny(ctx: TenantContext, message: str) -> HTTPException:
        platform.metrics["denied"] += 1
        platform.log("access_denied", ctx.tenant_id)
        return HTTPException(403, message)

    @app.post("/v1/infer")
    def infer(body: InferRequest, response: Response, ctx: TenantContext = Depends(context)):
        if ctx.role != "service":
            raise deny(ctx, "service role required")
        if body.tenant_id and body.tenant_id != ctx.tenant_id:
            raise deny(ctx, "token does not match requested tenant")
        model, version = platform.model_for(ctx)
        sources = platform.search(ctx, body.text)
        platform.log("infer", ctx.tenant_id, version=version, chars=len(body.text))
        response.headers["X-Model-Version"] = version
        return {"label": predict(model, [body.text])[0], "model_version": version,
                "sources": [s["text"] for s in sources]}

    @app.get("/v1/tenants/{tenant_id}/versions")
    def versions(tenant_id: str, ctx: TenantContext = Depends(context)):
        if ctx.role != "service":
            raise deny(ctx, "service role required")
        try:
            return {"versions": platform.registry.versions(ctx, tenant_id),
                    "prod": platform.registry.prod_version(ctx, tenant_id)}
        except AccessDenied as exc:
            raise deny(ctx, str(exc)) from exc

    @app.get("/v1/admin/metrics")
    def metrics(ctx: TenantContext = Depends(context)):
        if ctx.role != "admin":
            raise deny(ctx, "admin role required")
        return platform.metrics

    @app.post("/v1/admin/break-glass")
    def break_glass(body: BreakGlassRequest, ctx: TenantContext = Depends(context)):
        if ctx.role != "admin":
            raise deny(ctx, "admin role required")
        if not body.reason.strip():
            raise HTTPException(400, "a reason is required")
        if not platform.keyring.has(body.tenant_id):
            raise HTTPException(404, "unknown tenant")
        platform.log("break_glass", body.tenant_id, by=tenant_hash(ctx.tenant_id, platform.log_salt), reason=body.reason)
        tenant_ctx = TenantContext(body.tenant_id)
        return {"record_count": len(platform.store(body.tenant_id).records(tenant_ctx))}

    return app
