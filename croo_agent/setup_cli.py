"""One-time Croo Provider setup + service catalogue rebuild.

Modes:

  Phase A — wallet bootstrap (no `CROO_WALLET_PRIVATE_KEY` in .env yet):
    Generate a fresh EOA, print the private key and `.env` line to add, exit
    non-zero so the operator can fund the address before continuing.

  Phase B — fresh setup (`CROO_WALLET_PRIVATE_KEY` is set, no `.credentials.json`):
    1. UserClient.setup_agent → deploys navigator + agent + first service +
       returns SDK-Key (slow ~60s due to two on-chain confirmations)
    2. create_service ×(N-1) for the remaining services (~150ms each, off-chain)
    3. Persist `{service_id → spec_slug}` to `croo_agent/.credentials.json` v2

  Rebuild (`--rebuild`, requires existing `.credentials.json`):
    Keeps the same agent_id / SDK-Key / AA wallet. Lists all current services,
    deactivates the active ones, then re-creates the catalogue from
    `services.SPECS`. Use this to refresh the service split without redeploying
    the agent on-chain. Operator must restart `python -m croo_agent` afterwards.

Run with:
    python -m croo_agent.setup_cli                # fresh setup
    python -m croo_agent.setup_cli --rebuild      # refresh service catalogue
    python -m croo_agent.setup_cli --force        # skip confirm prompt
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from core.config import get_settings
from croo_agent import credentials as creds_mod
from croo_agent.services import ServiceSpec, get_service_specs

logger = logging.getLogger(__name__)


def _generate_wallet_and_exit() -> int:
    """Phase A — generate a wallet, print instructions, exit."""
    from eth_account import Account

    acct = Account.create()
    address = acct.address
    private_key = acct.key.hex()  # 0x-prefixed hex (HexBytes 1.x default)

    print()
    print("=" * 72)
    print("  Croo Provider Setup — Phase A: New wallet generated")
    print("=" * 72)
    print()
    print(f"  Address:      {address}")
    print(f"  Private key:  {private_key}")
    print()
    print("  ▸ Add this line to your .env file (KEEP THIS SECRET):")
    print()
    print(f'      CROO_WALLET_PRIVATE_KEY={private_key}')
    print()
    print("  ▸ Then fund the address on the Croo dev chain with:")
    print("      • Native gas token (for AA wallet deployment + accept_negotiation tx)")
    print("      • USDC on the dev chain (only required for *consumer* role; provider")
    print("        receives USDC, does not pay)")
    print()
    print("  ▸ Once funded, re-run:  python -m croo_agent.setup_cli")
    print()
    print("=" * 72)
    return 1  # exit non-zero so CI doesn't accidentally proceed


def _confirm_overwrite(path: Path, force: bool) -> bool:
    if not path.exists():
        return True
    if force:
        return True
    print(f"\n⚠  Existing credentials at {path}")
    print("   Re-running setup will OVERWRITE them. The old SDK-Key will keep working")
    print("   but the local file will lose the old service_id → capability mapping.")
    answer = input("   Continue? [y/N] ").strip().lower()
    return answer in ("y", "yes")


async def _register_services(
    user_client,
    spec_list: list[ServiceSpec],
    payment_token: str,
) -> tuple[str, str, str, str, dict[str, str]]:
    """Fresh-setup path: setup_agent for the first service + create_service for the rest.

    Returns: (agent_id, sdk_key, wallet_address, controller_address, {service_id: spec_slug}).

    Note: `setup_agent` internally activates the first service, but plain
    `create_service` leaves the rest in `draft`. We explicitly call
    `update_service(status=ACTIVE)` on every newly-created service so the full
    catalogue is discoverable on the marketplace.
    """
    from croo import (
        CreateServiceRequest,
        ServiceStatus,
        SetupAgentRequest,
        UpdateServiceRequest,
    )

    if not spec_list:
        raise RuntimeError("No services to register — get_service_specs() returned empty")

    first = spec_list[0]
    logger.info(
        "Calling setup_agent (deploys AA wallet + registers first service: %s)",
        first.name,
    )
    setup_result = await user_client.setup_agent(SetupAgentRequest(
        agent_name="Polymarket Broker",
        agent_description=(
            "Provider agent exposing Polymarket Broker capabilities (market query, "
            "data feed, convergence-arbitrage scanner, AI analysis) on the Croo "
            "decentralized marketplace. Each capability is exposed as multiple "
            "fine-grained services so buyers can pick exactly the data they need."
        ),
        service_name=first.name,
        service_desc=first.description,
        service_price=first.price_str(),
        sla_minutes=first.sla_minutes,
        payment_token=payment_token,
        order_type=first.order_type,
        requirement=first.requirement_schema_json(),
        deliverable_type=first.deliverable_type,
    ))

    agent = setup_result.agent
    sdk_key = setup_result.sdk_key
    first_service = setup_result.service

    service_map: dict[str, str] = {first_service.service_id: first.slug}

    # Register remaining services one-by-one (dev API may rate-limit, so no gather).
    # Each newly-created service comes back as draft — we activate it immediately
    # so the catalogue is fully live after `setup_cli` finishes.
    total = len(spec_list)
    for idx, spec in enumerate(spec_list[1:], start=2):
        logger.info("[%d/%d] Registering service: %s", idx, total, spec.name)
        svc = await user_client.create_service(agent.agent_id, CreateServiceRequest(
            name=spec.name,
            description=spec.description,
            price=spec.price_str(),
            sla_minutes=spec.sla_minutes,
            payment_token=payment_token,
            order_type=spec.order_type,
            requirement=spec.requirement_schema_json(),
            deliverable_type=spec.deliverable_type,
        ))
        service_map[svc.service_id] = spec.slug

        try:
            await user_client.update_service(
                svc.service_id,
                UpdateServiceRequest(status=ServiceStatus.ACTIVE),
            )
        except Exception:
            logger.warning(
                "update_service(%s, ACTIVE) failed; service may stay in draft",
                svc.service_id,
            )

    return (
        agent.agent_id,
        sdk_key,
        agent.wallet_address,
        agent.controller_address,
        service_map,
    )


async def _rebuild_services(
    user_client,
    creds: "creds_mod.Credentials",
    spec_list: list[ServiceSpec],
    payment_token: str,
) -> dict[str, str]:
    """Rebuild path: deactivate existing services + re-create the catalogue.

    Keeps the same agent_id, SDK-Key, and AA wallet — only the service catalogue
    changes. Returns the new {service_id: spec_slug} map.
    """
    from croo import CreateServiceRequest, ServiceStatus, UpdateServiceRequest

    # 1) login (no-op for navigator if already deployed)
    login_result = await user_client.login()
    logger.info("login ok user_id=%s navigator_status=%s",
                login_result.user_id, login_result.navigator_status)

    # 2) list existing services on this agent
    try:
        existing = await user_client.list_services(creds.agent_id)
    except Exception as exc:
        logger.exception("list_services(%s) failed", creds.agent_id)
        raise RuntimeError(f"Could not list existing services: {exc}") from exc
    logger.info("Found %d existing service(s) on agent %s", len(existing), creds.agent_id)

    # 3) deactivate every active one
    deactivated = 0
    for svc in existing:
        status = (getattr(svc, "status", "") or "").lower()
        if status == "active":
            logger.info("Deactivating service %s (%s)", svc.service_id, svc.name)
            try:
                await user_client.update_service(
                    svc.service_id,
                    UpdateServiceRequest(status=ServiceStatus.INACTIVE),
                )
                deactivated += 1
            except Exception:
                logger.exception("update_service(%s, INACTIVE) failed; continuing", svc.service_id)
    logger.info("Deactivated %d service(s)", deactivated)

    # 4) create the new fine-grained catalogue
    new_map: dict[str, str] = {}
    total = len(spec_list)
    for idx, spec in enumerate(spec_list, start=1):
        logger.info("[%d/%d] Creating service: %s (slug=%s)", idx, total, spec.name, spec.slug)
        try:
            svc = await user_client.create_service(creds.agent_id, CreateServiceRequest(
                name=spec.name,
                description=spec.description,
                price=spec.price_str(),
                sla_minutes=spec.sla_minutes,
                payment_token=payment_token,
                order_type=spec.order_type,
                requirement=spec.requirement_schema_json(),
                deliverable_type=spec.deliverable_type,
            ))
        except Exception as exc:
            logger.exception("create_service(%s) failed; aborting rebuild", spec.slug)
            raise RuntimeError(
                f"create_service failed at slug {spec.slug!r} ({idx}/{total}): {exc}. "
                f"Some services were already created — re-run with --rebuild to retry."
            ) from exc
        new_map[svc.service_id] = spec.slug

        # If create_service yielded a draft, explicitly activate so buyers can find it.
        try:
            await user_client.update_service(
                svc.service_id,
                UpdateServiceRequest(status=ServiceStatus.ACTIVE),
            )
        except Exception:
            logger.warning("update_service(%s, ACTIVE) failed (may already be active)", svc.service_id)

    return new_map


async def _run_setup(force: bool, rebuild: bool) -> int:
    settings = get_settings()
    if not settings.croo_wallet_private_key:
        return _generate_wallet_and_exit()
    if not settings.croo_payment_token:
        logger.warning("CROO_PAYMENT_TOKEN is empty — passing empty string to create_service (dev API may reject)")
    if not settings.croo_rpc_url:
        logger.warning("CROO_RPC_URL is empty — SDK will use its default (likely Base mainnet, may not match dev chain)")

    from croo import Config, PrivateKeySigner, UserClient

    signer = PrivateKeySigner(settings.croo_wallet_private_key)
    user_client = UserClient(
        Config(
            base_url=settings.croo_api_base,
            ws_url=settings.croo_ws_url,
            rpc_url=settings.croo_rpc_url,
        ),
        signer,
    )

    if rebuild:
        # Rebuild path: keep existing agent, refresh service catalogue.
        try:
            existing_creds = creds_mod.load()
        except creds_mod.CredentialsMissing as exc:
            print(f"✗ Cannot rebuild — no existing credentials: {exc}", file=sys.stderr)
            await user_client.close()
            return 2

        if not _confirm_overwrite(creds_mod.DEFAULT_PATH, force):
            print("Aborted.")
            await user_client.close()
            return 0

        try:
            spec_list = get_service_specs()
            new_service_map = await _rebuild_services(
                user_client, existing_creds, spec_list, settings.croo_payment_token,
            )
            # Refresh wallet + controller addresses from the live agent in case they
            # changed (e.g. a prior `.credentials.json` pre-dates this schema change).
            try:
                live_agent = await user_client.get_agent(existing_creds.agent_id)
                existing_creds.wallet_address = live_agent.wallet_address
                existing_creds.controller_address = live_agent.controller_address
            except Exception:
                logger.warning(
                    "get_agent(%s) failed after rebuild; keeping existing wallet/controller",
                    existing_creds.agent_id,
                )
        finally:
            await user_client.close()

        existing_creds.services = new_service_map
        existing_creds.generated_at = creds_mod.now_iso()
        existing_creds.schema_version = creds_mod.SCHEMA_VERSION
        if not existing_creds.eoa_address:
            existing_creds.eoa_address = _derive_eoa_address(settings.croo_wallet_private_key)
        creds_mod.save(existing_creds)

        _print_done_banner(
            agent_id=existing_creds.agent_id,
            wallet_address=existing_creds.wallet_address,
            controller_address=existing_creds.controller_address,
            eoa_address=existing_creds.eoa_address,
            sdk_key=existing_creds.sdk_key,
            service_map=new_service_map,
            mode="rebuild",
        )
        return 0

    # Fresh setup path
    if not _confirm_overwrite(creds_mod.DEFAULT_PATH, force):
        print("Aborted.")
        await user_client.close()
        return 0

    try:
        spec_list = get_service_specs()
        (
            agent_id,
            sdk_key,
            wallet_address,
            controller_address,
            service_map,
        ) = await _register_services(
            user_client, spec_list, settings.croo_payment_token,
        )
    finally:
        await user_client.close()

    eoa_address = _derive_eoa_address(settings.croo_wallet_private_key)

    creds = creds_mod.Credentials(
        agent_id=agent_id,
        sdk_key=sdk_key,
        wallet_address=wallet_address,
        controller_address=controller_address,
        eoa_address=eoa_address,
        services=service_map,
        environment="dev",
        generated_at=creds_mod.now_iso(),
        schema_version=creds_mod.SCHEMA_VERSION,
    )
    creds_mod.save(creds)

    _print_done_banner(
        agent_id=agent_id,
        wallet_address=wallet_address,
        controller_address=controller_address,
        eoa_address=eoa_address,
        sdk_key=sdk_key,
        service_map=service_map,
        mode="fresh",
    )
    return 0


def _derive_eoa_address(private_key: str) -> str:
    """Return the 0x-prefixed EOA address derived from the private key in .env."""
    if not private_key:
        return ""
    try:
        from eth_account import Account
        return Account.from_key(private_key).address
    except Exception:
        return ""


def _print_done_banner(*, agent_id: str, wallet_address: str,
                       controller_address: str, eoa_address: str,
                       sdk_key: str, service_map: dict[str, str], mode: str) -> None:
    print()
    print("=" * 72)
    label = "rebuilt" if mode == "rebuild" else "setup complete"
    print(f"  ✓ Croo Provider {label}")
    print("=" * 72)
    print(f"  Agent ID:            {agent_id}")
    print(f"  Agent AA wallet:     {wallet_address}")
    print(f"  Controller address:  {controller_address}")
    print(f"  EOA (Controller's    {eoa_address}")
    print(f"      owner / signer):")
    print(f"  SDK-Key:             {sdk_key[:14]}…  (full value in .credentials.json)")
    print(f"  Services:            {len(service_map)} registered")
    for sid, slug in service_map.items():
        print(f"    - {slug:<28} {sid}")
    print()
    print(f"  Credentials saved to:")
    print(f"    {creds_mod.DEFAULT_PATH}")
    print()
    if mode == "rebuild":
        print("  Restart the provider to pick up the new service catalogue:")
        print("    python -m croo_agent")
    else:
        print("  Next:  python -m croo_agent")
    print("=" * 72)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Croo Provider setup / rebuild")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing .credentials.json without prompting")
    parser.add_argument("--rebuild", action="store_true",
                        help="Rebuild the service catalogue on an existing agent (keeps "
                             "agent_id / SDK-Key / AA wallet; deactivates current services "
                             "and re-creates them from croo_agent.services.SPECS)")
    args = parser.parse_args()
    try:
        return asyncio.run(_run_setup(args.force, args.rebuild))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
