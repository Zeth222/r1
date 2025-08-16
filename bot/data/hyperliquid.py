"""Minimal Hyperliquid API client."""
from __future__ import annotations

import asyncio
import httpx
from typing import Any, Dict

from hyperliquid.info import Info
from hyperliquid.utils import constants

from ..config import get_settings


_info = Info(constants.MAINNET_API_URL)


async def fetch_account(address: str) -> Dict[str, Any]:
    """Fetch full account state via Hyperliquid SDK."""
    return await asyncio.to_thread(_info.user_state, address)


async def fetch_positions(address: str) -> Dict[str, Any]:
    """Fetch positions for the given account."""
    state = await asyncio.to_thread(_info.user_state, address)
    return state.get("assetPositions", [])


async def place_order(client: httpx.AsyncClient, *, symbol: str, size: float, side: str, price: float | None = None) -> Dict[str, Any]:
    settings = get_settings()
    if settings.MODE == "viewer":
        return {"status": "simulated"}
    payload = {"symbol": symbol, "size": size, "side": side, "price": price}
    resp = await client.post(f"{constants.MAINNET_API_URL}/orders", json=payload)
    resp.raise_for_status()
    return resp.json()
