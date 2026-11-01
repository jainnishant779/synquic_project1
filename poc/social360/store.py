"""Per-tenant encrypted storage, keyed retrieval and offboarding.

Isolation here is logical and on one machine. Each tenant has its own directory, its own key and
its own retrieval index, and every call requires a TenantContext for that tenant.

Crypto note: the keystream below is HMAC-SHA256 in counter mode with an HMAC tag, written with the
standard library so the POC adds no compiled dependency. Production uses KMS envelope encryption
with AES-GCM [DESIGN]. Do not reuse this cipher outside the demo.
"""
import hashlib
import hmac
import json
import math
import re
import secrets
import shutil
from collections import Counter
from pathlib import Path

from .tenancy import AccessDenied, TenantContext

TOKEN = re.compile(r"[a-z0-9_]+")
TENANT_ID = re.compile(r"[a-z0-9_]{1,64}")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = (hmac.new(key, nonce + i.to_bytes(8, "big"), hashlib.sha256).digest()
              for i in range(length // 32 + 1))
    return b"".join(blocks)[:length]


def encrypt(key: bytes, plaintext: bytes) -> bytes:
    nonce = secrets.token_bytes(16)
    body = bytes(a ^ b for a, b in zip(plaintext, _keystream(key, nonce, len(plaintext))))
    tag = hmac.new(key, nonce + body, hashlib.sha256).digest()
    return nonce + tag + body


def decrypt(key: bytes, blob: bytes) -> bytes:
    nonce, tag, body = blob[:16], blob[16:48], blob[48:]
    if not hmac.compare_digest(tag, hmac.new(key, nonce + body, hashlib.sha256).digest()):
        raise AccessDenied("decryption failed: wrong key or tampered data")
    return bytes(a ^ b for a, b in zip(body, _keystream(key, nonce, len(body))))


class TenantStore:
    """All data for one tenant. Holds no reference to any other tenant."""

    def __init__(self, root: Path, tenant_id: str, keyring: "KeyRing"):
        if not TENANT_ID.fullmatch(tenant_id):
            raise AccessDenied("invalid tenant id")
        self.tenant_id = tenant_id
        self.dir = Path(root) / tenant_id
        self._keyring = keyring

    def _authorize(self, ctx: TenantContext) -> bytes:
        if ctx.tenant_id != self.tenant_id:
            raise AccessDenied(f"{ctx.tenant_id} may not access {self.tenant_id}")
        return self._keyring.key_for(self.tenant_id)

    def _read(self, ctx: TenantContext) -> list[dict]:
        key = self._authorize(ctx)
        path = self.dir / "records.enc"
        return json.loads(decrypt(key, path.read_bytes())) if path.exists() else []

    def add(self, ctx: TenantContext, records: list[dict]) -> None:
        key = self._authorize(ctx)
        merged = self._read(ctx) + records
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "records.enc").write_bytes(encrypt(key, json.dumps(merged).encode()))

    def records(self, ctx: TenantContext) -> list[dict]:
        return self._read(ctx)

    def search(self, ctx: TenantContext, query: str, limit: int = 3) -> list[dict]:
        """BM25 over this tenant's decrypted records. There is no index, shared or otherwise."""
        records = self._read(ctx)
        documents = [Counter(tokenize(r["text"])) for r in records]
        if not documents:
            return []
        average = sum(sum(d.values()) for d in documents) / len(documents)
        scores = []
        for record, document in zip(records, documents):
            score = 0.0
            for term in tokenize(query):
                frequency = document.get(term, 0)
                if frequency:
                    containing = sum(1 for d in documents if term in d)
                    idf = math.log(1 + (len(documents) - containing + 0.5) / (containing + 0.5))
                    length = sum(document.values())
                    score += idf * frequency * 2.2 / (frequency + 1.2 * (0.25 + 0.75 * length / average))
            if score > 0:
                scores.append((score, record))
        return [record for _, record in sorted(scores, key=lambda s: -s[0])[:limit]]


class KeyRing:
    """One random key per tenant. Stands in for a KMS [DESIGN]."""

    def __init__(self):
        self._keys: dict[str, bytes] = {}

    def create(self, tenant_id: str) -> None:
        self._keys.setdefault(tenant_id, secrets.token_bytes(32))

    def has(self, tenant_id: str) -> bool:
        return tenant_id in self._keys

    def key_for(self, tenant_id: str) -> bytes:
        if tenant_id not in self._keys:
            raise AccessDenied(f"no key for {tenant_id}")
        return self._keys[tenant_id]

    def destroy(self, tenant_id: str) -> None:
        self._keys.pop(tenant_id, None)


def offboard(root: Path, tenant_id: str, keyring: KeyRing) -> None:
    """Remove a tenant's store, adapters and registry entries, then destroy its key."""
    directory = Path(root) / tenant_id
    if directory.exists():
        shutil.rmtree(directory)
    keyring.destroy(tenant_id)
