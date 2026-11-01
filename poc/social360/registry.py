"""Model registry: immutable versions per tenant, with an atomically moved prod pointer."""
import json
import os
import shutil
from pathlib import Path

from .tenancy import AccessDenied, TenantContext


class Registry:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _tenant_dir(self, ctx: TenantContext, tenant_id: str) -> Path:
        if ctx.tenant_id != tenant_id:
            raise AccessDenied(f"{ctx.tenant_id} may not access versions of {tenant_id}")
        return self.root / tenant_id / "registry"

    def versions(self, ctx: TenantContext, tenant_id: str) -> list[str]:
        directory = self._tenant_dir(ctx, tenant_id)
        return sorted(p.name for p in directory.glob("v*") if p.is_dir()) if directory.exists() else []

    def register(self, ctx: TenantContext, tenant_id: str, adapter: Path | None, metadata: dict) -> str:
        """Record a version. adapter is None when the artefact must not be kept, such as after a leak."""
        directory = self._tenant_dir(ctx, tenant_id)
        version = f"v{len(self.versions(ctx, tenant_id)) + 1:04d}"
        target = directory / version
        target.mkdir(parents=True, exist_ok=False)
        if adapter is not None:
            shutil.copyfile(adapter, target / "adapter.pt")
        (target / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        return version

    def metadata(self, ctx: TenantContext, tenant_id: str, version: str) -> dict:
        path = self._tenant_dir(ctx, tenant_id) / version / "metadata.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def promote(self, ctx: TenantContext, tenant_id: str, version: str) -> None:
        directory = self._tenant_dir(ctx, tenant_id)
        if not (directory / version).is_dir():
            raise ValueError(f"unknown version {version}")
        history = self._history(directory) + [version]
        temporary = directory / "prod.tmp"
        temporary.write_text(json.dumps(history), encoding="utf-8")
        os.replace(temporary, directory / "prod.json")

    def rollback(self, ctx: TenantContext, tenant_id: str) -> str:
        directory = self._tenant_dir(ctx, tenant_id)
        history = self._history(directory)
        if len(history) < 2:
            raise ValueError("no earlier production version")
        temporary = directory / "prod.tmp"
        temporary.write_text(json.dumps(history[:-1]), encoding="utf-8")
        os.replace(temporary, directory / "prod.json")
        return history[-2]

    @staticmethod
    def _history(directory: Path) -> list[str]:
        path = directory / "prod.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def prod_version(self, ctx: TenantContext, tenant_id: str) -> str | None:
        history = self._history(self._tenant_dir(ctx, tenant_id))
        return history[-1] if history else None

    def adapter_path(self, ctx: TenantContext, tenant_id: str, version: str) -> Path:
        return self._tenant_dir(ctx, tenant_id) / version / "adapter.pt"
