"""Command-line entrypoint for Hyperliquid interactions.

The script reads configuration from environment variables and only sends real
orders when running in ``LIVE`` mode with ``HL_PRIVATE_KEY`` defined. In other
modes it logs what would be executed.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

from hyperliquid_client import get_hl_open_positions, place_order, cancel_order

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODE = os.getenv("MODE", "SAFE").upper()


def safe_place_order(
    symbol: str, side: str, size: float, price: Optional[float] = None, reduce_only: bool = False
):
    """Place an order respecting the current running mode."""
    if MODE == "LIVE" and os.getenv("HL_PRIVATE_KEY"):
        return place_order(symbol, side, size, price, reduce_only)
    logger.info(
        "executaria ordem %s %s size=%s price=%s, mas em modo %s",
        side,
        symbol,
        size,
        price,
        MODE,
    )
    return {"status": "simulated"}


def safe_cancel_order(order_id: str):
    """Cancel an order respecting the running mode."""
    if MODE == "LIVE" and os.getenv("HL_PRIVATE_KEY"):
        return cancel_order(order_id)
    logger.info("executaria cancelamento %s, mas em modo %s", order_id, MODE)
    return {"status": "simulated"}


def main() -> None:
    wallet = os.getenv("HL_WALLET_ADDRESS")
    if wallet:
        positions = get_hl_open_positions(wallet)
        logger.info("open positions: %s", positions)
    else:
        logger.info("HL_WALLET_ADDRESS not configured")

    # Example placeholder
    safe_place_order("ETH", "buy", 1.0, price=None)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
