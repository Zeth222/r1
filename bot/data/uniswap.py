"""Utilities to read Uniswap v3 positions via The Graph."""
from __future__ import annotations

import math
from typing import Any, Dict, List

import httpx

from ..config import get_settings


QUERY = """
query($owner: String!) {
  positions(where: {owner: $owner}) {
    id
    liquidity
    tickLower { tick }
    tickUpper { tick }
    pool { sqrtPrice token0 { symbol decimals } token1 { symbol decimals } }
  }
}
"""


async def fetch_positions(client: httpx.AsyncClient, owner: str) -> List[Dict[str, Any]]:
    """Fetch positions from The Graph subgraph."""
    settings = get_settings()
    resp = await client.post(settings.UNISWAP_SUBGRAPH_URL, json={"query": QUERY, "variables": {"owner": owner}})
    resp.raise_for_status()
    data = resp.json()["data"]["positions"]
    return data


def tick_to_sqrt_price(tick: int) -> float:
    return math.pow(1.0001, tick / 2)


def liquidity_to_amounts(liq: float, sqrt_p: float, sqrt_lower: float, sqrt_upper: float) -> tuple[float, float]:
    """Compute token amounts from liquidity and price bounds."""
    if sqrt_p <= sqrt_lower:
        amount0 = liq * (sqrt_upper - sqrt_lower) / (sqrt_lower * sqrt_upper)
        amount1 = 0.0
    elif sqrt_p < sqrt_upper:
        amount0 = liq * (sqrt_upper - sqrt_p) / (sqrt_p * sqrt_upper)
        amount1 = liq * (sqrt_p - sqrt_lower)
    else:
        amount0 = 0.0
        amount1 = liq * (sqrt_upper - sqrt_lower)
    return amount0, amount1


def position_delta(position: Dict[str, Any]) -> float:
    """Return WETH exposure (positive if long WETH)."""
    pool = position["pool"]
    sqrt_price = float(pool["sqrtPrice"]) / (1 << 96)
    liq = float(position["liquidity"])
    sqrt_lower = tick_to_sqrt_price(int(position["tickLower"]["tick"]))
    sqrt_upper = tick_to_sqrt_price(int(position["tickUpper"]["tick"]))
    amount0, amount1 = liquidity_to_amounts(liq, sqrt_price, sqrt_lower, sqrt_upper)
    token0 = pool["token0"]["symbol"]
    token1 = pool["token1"]["symbol"]
    decimals0 = int(pool["token0"]["decimals"])
    decimals1 = int(pool["token1"]["decimals"])
    amount0 /= 10 ** decimals0
    amount1 /= 10 ** decimals1
    # assume token0=WETH token1=USDC
    price = (sqrt_price ** 2)
    exposure = amount0 - amount1 / price
    return exposure
