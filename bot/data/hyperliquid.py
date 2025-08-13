"""Minimal Hyperliquid API client."""
from __future__ import annotations

import httpx
from typing import Any, Dict

from ..config import get_settings


BASE_URL = "https://api.hyperliquid.xyz"  # placeholder


async def fetch_account(client: httpx.AsyncClient, address: str) -> Dict[str, Any]:
    resp = await client.get(f"{BASE_URL}/accounts/{address}")
    resp.raise_for_status()
    return resp.json()


async def fetch_positions(client: httpx.AsyncClient, address: str) -> Dict[str, Any]:
    resp = await client.get(f"{BASE_URL}/positions/{address}")
    resp.raise_for_status()
    return resp.json()


async def place_order(client: httpx.AsyncClient, *, symbol: str, size: float, side: str, price: float | None = None) -> Dict[str, Any]:
    settings = get_settings()
    if settings.MODE == "viewer":
        return {"status": "simulated"}
    payload = {"symbol": symbol, "size": size, "side": side, "price": price}
    resp = await client.post(f"{BASE_URL}/orders", json=payload)
    resp.raise_for_status()
    return resp.json()
