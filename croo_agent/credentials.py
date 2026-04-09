"""Persistence for Croo provider credentials.

Stores `agent_id`, `sdk_key`, `wallet_address`, and `service_id → capability` mapping
in a gitignored JSON file at `croo_agent/.credentials.json` (chmod 600).

Falls back to `core.config` env-var equivalents when the JSON file is absent — useful
for CI/Docker deployments where credentials come from a secrets manager.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path

from core.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent / ".credentials.json"

# v1 = `services: {service_id: capability_name}` (4 capability-grained services)
# v2 = `services: {service_id: spec_slug}` (N fine-grained services)
SCHEMA_VERSION = 2


class CredentialsMissing(RuntimeError):
    """Raised when neither the credentials file nor env-var fallbacks are populated."""


@dataclass
class Credentials:
    agent_id: str
    sdk_key: str
    wallet_address: str = ""        # Agent AA wallet (smart contract, receives USDC)
    controller_address: str = ""    # Agent's Croo-managed operator key (distinct from EOA and AA)
    eoa_address: str = ""           # User's EOA (derived from CROO_WALLET_PRIVATE_KEY)
    services: dict[str, str] = field(default_factory=dict)  # service_id → spec slug
    environment: str = "dev"
    generated_at: str = ""
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.schema_version,
            "agent_id": self.agent_id,
            "sdk_key": self.sdk_key,
            "wallet_address": self.wallet_address,
            "controller_address": self.controller_address,
            "eoa_address": self.eoa_address,
            "services": self.services,
            "environment": self.environment,
            "generated_at": self.generated_at,
        }


def save(creds: Credentials, path: Path = DEFAULT_PATH) -> None:
    """Atomic write + chmod 600. Overwrites any existing file at `path`."""
    payload = json.dumps(creds.to_dict(), indent=2, ensure_ascii=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".credentials.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    try:
        os.chmod(path, 0o600)
    except OSError:
        # Windows / readonly fs — non-fatal
        pass
    logger.info("Saved Croo credentials to %s", path)


def load(path: Path = DEFAULT_PATH) -> Credentials:
    """Load credentials from `path`. Raises CredentialsMissing if absent or unreadable.

    Tolerates both schema v1 (services map values are capability names) and
    schema v2 (services map values are spec slugs). On v1, the runtime startup
    code in `runtime.py` will fail to resolve any of the legacy capability values
    against `SPECS_BY_SLUG` and will tell the user to re-run `setup_cli --rebuild`.
    """
    if not path.exists():
        raise CredentialsMissing(f"Credentials file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise CredentialsMissing(f"Failed to read credentials at {path}: {exc}") from exc
    schema_version = int(data.get("version", 1))
    if schema_version == 1:
        logger.warning(
            "Loading legacy v1 credentials from %s — service map contains "
            "capability names, not slugs. Run `python -m croo_agent.setup_cli "
            "--rebuild` to upgrade to v2.",
            path,
        )
    return Credentials(
        agent_id=data.get("agent_id", ""),
        sdk_key=data.get("sdk_key", ""),
        wallet_address=data.get("wallet_address", ""),
        controller_address=data.get("controller_address", ""),
        eoa_address=data.get("eoa_address", ""),
        services=data.get("services", {}),
        environment=data.get("environment", "dev"),
        generated_at=data.get("generated_at", ""),
        schema_version=schema_version,
    )


def load_with_env_fallback(path: Path = DEFAULT_PATH) -> Credentials:
    """Load from `path` if present; otherwise build minimal Credentials from env-vars.

    The env fallback path has no service_id mapping, so dispatcher cannot resolve
    capabilities by service_id — runtime should refuse to start if `services` is empty.
    """
    try:
        return load(path)
    except CredentialsMissing:
        pass
    settings = get_settings()
    if not settings.croo_sdk_key or not settings.croo_agent_id:
        raise CredentialsMissing(
            f"No credentials at {path} and CROO_SDK_KEY/CROO_AGENT_ID not set in env"
        )
    return Credentials(
        agent_id=settings.croo_agent_id,
        sdk_key=settings.croo_sdk_key,
        wallet_address="",
        services={},
        environment="dev",
        generated_at="",
        schema_version=SCHEMA_VERSION,
    )


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
