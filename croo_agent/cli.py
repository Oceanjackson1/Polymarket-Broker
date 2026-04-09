"""Croo Provider runtime entry point.

Usage:
  python -m croo_agent              # full runtime
  python -m croo_agent --check      # Feilian connectivity dry-run
  python -m croo_agent --dry-run    # connect + listen but never call deliver_order
"""
from __future__ import annotations

import argparse
import asyncio
import logging

from croo_agent.runtime import run_provider

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Croo Provider for Polymarket Broker")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify Feilian connectivity to the Croo dev API and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Subscribe to events and run handlers, but do NOT call deliver_order",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(run_provider(check_only=args.check, dry_run=args.dry_run))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
