"""End-to-end smoke test as a Croo *buyer*.

Creates a lightweight buyer agent (no service of its own — buyers don't need one),
then negotiates an order against the local provider's `market_query` service. Lets
us validate the full NEGOTIATION_CREATED → ORDER_CREATED chain without needing a
second wallet.

Usage:
    .venv/bin/python -m croo_agent.buyer_smoke

Default behaviour:
- Uses the SAME controller wallet as the provider (CROO_WALLET_PRIVATE_KEY in .env)
  but creates a NEW agent under it (Croo dev rejects self-trade if both sides are
  the same agent_id)
- Caches the buyer agent_id + sdk_key in croo_agent/.buyer_credentials.json so
  re-runs are fast (no need to re-deploy on chain every time)
- Polls the negotiation/order state for up to 60s and prints transitions
- Optionally attempts pay_order (will fail if the buyer wallet has no USDC — that's
  expected; the goal here is verifying the off-chain signaling, not a real payment)

Flags:
    --capability {market_query|data_feed|strategy|analysis}   default: market_query
    --reset           force-create a fresh buyer agent (delete cached credentials)
    --pay             attempt pay_order after negotiation (expected to fail without USDC)
    --wait-seconds N  how long to poll before giving up (default 60)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path

from core.config import get_settings
from croo_agent.credentials import load as load_provider_creds

logger = logging.getLogger(__name__)

BUYER_CRED_PATH = Path(__file__).resolve().parent / ".buyer_credentials.json"


@dataclass
class BuyerCreds:
    agent_id: str
    sdk_key: str
    wallet_address: str
    generated_at: str

    def to_dict(self) -> dict:
        return self.__dict__


def _save_buyer(creds: BuyerCreds) -> None:
    BUYER_CRED_PATH.write_text(json.dumps(creds.to_dict(), indent=2), encoding="utf-8")
    try:
        BUYER_CRED_PATH.chmod(0o600)
    except OSError:
        pass


def _load_buyer() -> BuyerCreds | None:
    if not BUYER_CRED_PATH.exists():
        return None
    try:
        data = json.loads(BUYER_CRED_PATH.read_text(encoding="utf-8"))
        return BuyerCreds(**data)
    except Exception:
        return None


async def _create_buyer_agent(user_client) -> BuyerCreds:
    """Light-weight buyer creation: create_agent → deploy_agent → list_sdk_keys."""
    from croo import CreateAgentRequest, AgentStatus

    # Login first to discover navigator status
    login_result = await user_client.login()
    logger.info(
        "buyer login: user_id=%s navigator_status=%s",
        login_result.user_id, login_result.navigator_status,
    )
    if login_result.navigator_status == AgentStatus.CREATING:
        logger.info("deploying navigator (first time for this controller)...")
        await user_client.deploy_navigator()

    logger.info("creating buyer agent...")
    agent = await user_client.create_agent(CreateAgentRequest(
        name="Polymarket Broker — buyer smoke",
        description="Ephemeral buyer agent for end-to-end tests against the provider",
    ))
    logger.info("buyer agent created agent_id=%s; deploying AA wallet...", agent.agent_id)

    deploy_result = await user_client.deploy_agent(agent.agent_id)
    logger.info(
        "buyer agent deployed aa_address=%s tx_hash=%s",
        deploy_result.aa_address, deploy_result.tx_hash,
    )

    keys = await user_client.list_sdk_keys(agent.agent_id)
    if not keys:
        raise RuntimeError(f"buyer agent {agent.agent_id} has no SDK keys")
    sdk_key = keys[0].sdk_key

    creds = BuyerCreds(
        agent_id=agent.agent_id,
        sdk_key=sdk_key,
        wallet_address=deploy_result.aa_address,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    _save_buyer(creds)
    logger.info("buyer credentials cached at %s", BUYER_CRED_PATH)
    return creds


def _build_requirements_for_slug(slug: str) -> str:
    """Default buyer requirements for a service slug — derived from the spec's
    `example_requirement()`. Returns a JSON-encoded string ready for the SDK."""
    from croo_agent.services import get_spec
    spec = get_spec(slug)
    return json.dumps(spec.example_requirement())


def _resolve_service_id_by_slug(provider_creds, slug: str) -> str:
    for sid, s in provider_creds.services.items():
        if s == slug:
            return sid
    available = sorted(set(provider_creds.services.values()))
    raise RuntimeError(
        f"slug {slug!r} not in provider credentials. "
        f"Available ({len(available)}): {available}"
    )


async def _poll_until(client, *, negotiation_id: str, wait_seconds: int) -> dict:
    """Poll negotiation + (eventually) order state every 2s. Returns a transitions dict."""
    transitions: dict[str, str] = {}
    deadline = asyncio.get_event_loop().time() + wait_seconds
    last_neg_status = ""
    last_order_id = ""
    last_order_status = ""

    while asyncio.get_event_loop().time() < deadline:
        try:
            neg = await client.get_negotiation(negotiation_id)
        except Exception as e:
            logger.warning("get_negotiation error: %s", e)
            await asyncio.sleep(2)
            continue

        if neg.status != last_neg_status:
            ts = datetime.now(UTC).strftime("%H:%M:%S")
            logger.info("[%s] negotiation status: %s → %s", ts, last_neg_status or "(initial)", neg.status)
            transitions[neg.status] = ts
            last_neg_status = neg.status

        # Once accepted, the order_id is reachable via list_orders or directly
        if neg.status in ("accepted", "completed") and not last_order_id:
            try:
                from croo import ListOptions
                orders = await client.list_orders(ListOptions(role="buyer", page=1, page_size=10))
                for o in orders:
                    if o.service_id == neg.service_id:
                        last_order_id = o.order_id
                        break
            except Exception:
                pass
            if last_order_id:
                logger.info("found order_id=%s", last_order_id)

        if last_order_id:
            try:
                order = await client.get_order(last_order_id)
                if order.status != last_order_status:
                    ts = datetime.now(UTC).strftime("%H:%M:%S")
                    logger.info("[%s] order status: %s → %s", ts, last_order_status or "(initial)", order.status)
                    transitions[f"order:{order.status}"] = ts
                    last_order_status = order.status
                if order.status == "completed":
                    return transitions | {"_terminal": "order:completed", "_order_id": last_order_id}
                if order.status in ("rejected", "expired"):
                    return transitions | {"_terminal": f"order:{order.status}", "_order_id": last_order_id}
            except Exception as e:
                logger.warning("get_order error: %s", e)

        if neg.status == "rejected":
            return transitions | {"_terminal": "negotiation:rejected"}

        await asyncio.sleep(2)

    return transitions | {"_terminal": "timeout"}


async def main_async() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Croo buyer smoke test (per-slug)")
    parser.add_argument("--service", default=None,
                        help="Slug of the service to buy (e.g. nba_list, market_search). "
                             "Run with --list-services to see all available slugs.")
    parser.add_argument("--list-services", action="store_true",
                        help="Print all service slugs from .credentials.json (provider side) "
                             "alongside the SPECS catalogue, then exit.")
    parser.add_argument("--requirements", default=None,
                        help="JSON string for buyer requirements override "
                             "(e.g. '{\"game_id\":\"...\"}'). If omitted, uses the spec's "
                             "example_requirement().")
    parser.add_argument("--reset", action="store_true", help="force-create a fresh buyer agent")
    parser.add_argument("--pay", action="store_true", help="attempt pay_order (likely fails: no USDC)")
    parser.add_argument("--wait-seconds", type=int, default=60)
    args = parser.parse_args()

    settings = get_settings()

    # Cheap path: just list available slugs and exit (no wallet / network needed)
    if args.list_services:
        try:
            provider_creds = load_provider_creds()
        except Exception as exc:
            print(f"✗ Could not read provider .credentials.json: {exc}", file=sys.stderr)
            return 2
        from croo_agent.services import SPECS_BY_SLUG
        print(f"Provider has {len(provider_creds.services)} service(s) registered.")
        print(f"SPECS catalogue defines {len(SPECS_BY_SLUG)} slug(s).")
        print()
        print(f"{'slug':<32} {'in catalogue':<14} {'in provider creds'}")
        print(f"{'-'*32} {'-'*14} {'-'*40}")
        provider_slugs = set(provider_creds.services.values())
        all_slugs = sorted(set(SPECS_BY_SLUG.keys()) | provider_slugs)
        for slug in all_slugs:
            in_cat = "yes" if slug in SPECS_BY_SLUG else "no"
            sids = [sid for sid, s in provider_creds.services.items() if s == slug]
            in_prov = sids[0] if sids else "—"
            print(f"{slug:<32} {in_cat:<14} {in_prov}")
        return 0

    if not args.service:
        print("✗ --service <slug> is required (or use --list-services). "
              "Example: --service nba_list", file=sys.stderr)
        return 2

    if not settings.croo_wallet_private_key:
        print("✗ CROO_WALLET_PRIVATE_KEY not set in .env", file=sys.stderr)
        return 2

    provider_creds = load_provider_creds()
    try:
        service_id = _resolve_service_id_by_slug(provider_creds, args.service)
    except RuntimeError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2
    logger.info("provider service_id (%s) = %s", args.service, service_id)

    from croo import (
        AgentClient,
        Config,
        NegotiateOrderRequest,
        PrivateKeySigner,
        UserClient,
    )

    config = Config(
        base_url=settings.croo_api_base,
        ws_url=settings.croo_ws_url,
        rpc_url=settings.croo_rpc_url,
    )

    # 1) Get-or-create buyer creds
    if args.reset and BUYER_CRED_PATH.exists():
        BUYER_CRED_PATH.unlink()
        logger.info("removed cached buyer creds")
    buyer = _load_buyer()
    if buyer is None:
        signer = PrivateKeySigner(settings.croo_wallet_private_key)
        user_client = UserClient(config, signer)
        try:
            buyer = await _create_buyer_agent(user_client)
        finally:
            await user_client.close()
    else:
        logger.info("reusing cached buyer agent_id=%s wallet=%s", buyer.agent_id, buyer.wallet_address)

    # 2) Buyer AgentClient → negotiate
    buyer_client = AgentClient(config, buyer.sdk_key)
    try:
        requirements = args.requirements if args.requirements is not None else _build_requirements_for_slug(args.service)
        logger.info("buyer.negotiate_order(service=%s slug=%s, requirements=%s)",
                    service_id, args.service, requirements)
        neg = await buyer_client.negotiate_order(NegotiateOrderRequest(
            service_id=service_id,
            requirements=requirements,
        ))
        logger.info(
            "✓ negotiation created: %s status=%s requester=%s provider=%s",
            neg.negotiation_id, neg.status, neg.requester_agent_id, neg.provider_agent_id,
        )

        # 3) Poll for state transitions
        transitions = await _poll_until(buyer_client, negotiation_id=neg.negotiation_id, wait_seconds=args.wait_seconds)

        # 4) Optional pay
        if args.pay and "accepted" in transitions:
            order_id = transitions.get("_order_id")
            if order_id:
                logger.info("attempting pay_order(%s) — expected to fail without USDC", order_id)
                try:
                    pay_result = await buyer_client.pay_order(order_id)
                    logger.info("✓ pay_order succeeded: tx=%s", pay_result.tx_hash)
                except Exception as exc:
                    logger.warning("pay_order failed (expected if buyer has no USDC): %s", exc)

        # 5) Final report
        print()
        print("=" * 72)
        print("  Buyer smoke test report")
        print("=" * 72)
        print(f"  service slug:    {args.service}")
        print(f"  service_id:      {service_id}")
        print(f"  requirements:    {requirements}")
        print(f"  negotiation_id:  {neg.negotiation_id}")
        print(f"  buyer_agent_id:  {buyer.agent_id}")
        print(f"  provider_agent:  {provider_creds.agent_id}")
        print(f"  state transitions:")
        for k, v in transitions.items():
            if not k.startswith("_"):
                print(f"    {v}  →  {k}")
        print(f"  terminal state:  {transitions.get('_terminal')}")
        print("=" * 72)
        return 0
    finally:
        await buyer_client.close()


def main() -> int:
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
