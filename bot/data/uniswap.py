"""Robust helpers for querying Uniswap v3 data via The Graph.

This module wraps the subgraph calls with strict validation so that a
missing or malformed payload never crashes the bot.  The original
implementation assumed the presence of ``response["data"][...]`` which
raised ``'NoneType' object is not subscriptable`` when the subgraph was
unavailable.  All accesses are now guarded and return ``None`` or empty
structures instead of raising.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import get_settings


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GraphQL queries
# ---------------------------------------------------------------------------

POSITIONS_QUERY = """
query Positions($owner: Bytes!, $first: Int!, $lastId: ID) {
  positions(
    first: $first
    where: { owner: $owner, id_gt: $lastId }
    orderBy: id
    orderDirection: asc
  ) {
    id
    liquidity
    depositedToken0
    depositedToken1
    withdrawnToken0
    withdrawnToken1
    collectedFeesToken0
    collectedFeesToken1
    token0 { id symbol decimals }
    token1 { id symbol decimals }
    pool {
      id
      feeTier
      sqrtPrice
      tick
      token0 { id symbol decimals }
      token1 { id symbol decimals }
    }
    tickLower { tickIdx tick }
    tickUpper { tickIdx tick }
  }
}
"""


POOL_QUERY = """
query Pool($poolId: ID!) {
  pool(id: $poolId) {
    id
    sqrtPrice
    tick
    liquidity
    token0 { symbol decimals }
    token1 { symbol decimals }
  }
}
"""


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def safe_json(response: httpx.Response) -> tuple[bool, Optional[Dict[str, Any]], str]:
    """Safely parse JSON responses.

    Returns a tuple ``(ok, json_data|None, error)``.  HTTP errors, invalid
    content type or JSON parsing failures are captured and returned as a
    string instead of raising.
    """

    try:
        if not 200 <= response.status_code < 300:
            return False, None, f"HTTP {response.status_code}"
        ctype = response.headers.get("content-type", "")
        if "application/json" not in ctype:
            return False, None, f"invalid content-type: {ctype}"
        return True, response.json(), ""
    except Exception as exc:  # pragma: no cover - defensive
        return False, None, str(exc)


def require_field(obj: Any, path: List[str]) -> tuple[Optional[Any], str]:
    """Navigate ``obj`` safely following ``path``.

    Returns the found value or ``None`` with an explanatory error string if
    any component is missing.
    """

    cur = obj
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None, f"missing field {'.'.join(path)}"
    return cur, ""


def _subgraph_url() -> Optional[str]:
    """Return Uniswap subgraph URL with API key if available."""

    settings = get_settings()
    url = settings.UNISWAP_SUBGRAPH_URL
    if not url:
        return None
    url = str(url)
    api_key = settings.THEGRAPH_API_KEY or os.getenv("THEGRAPH_API_KEY")
    if api_key and "/api/" in url and f"/{api_key}/" not in url:
        url = url.replace("/api/", f"/api/{api_key}/", 1)
    return url


@retry(
    wait=wait_exponential(multiplier=1, min=1),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.HTTPError, ValueError)),
)
async def graphql_query(
    session: httpx.AsyncClient, url: str, query: str, variables: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a GraphQL POST with retry/backoff."""

    headers = {"content-type": "application/json"}
    api_key = os.getenv("THEGRAPH_API_KEY")
    if api_key:
        headers["apikey"] = api_key

    start = time.perf_counter()
    resp = await session.post(url, json={"query": query, "variables": variables}, headers=headers)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    ok, payload, err = safe_json(resp)
    if not ok:
        sample = resp.text[:200].replace("\n", " ")
        logger.warning(
            json.dumps(
                {
                    "source": "uniswap",
                    "reason": err,
                    "http_status": resp.status_code,
                    "has_data": False,
                    "elapsed_ms": elapsed_ms,
                    "body_sample": sample,
                }
            )
        )
        raise ValueError(err)

    if "errors" in payload:
        logger.warning(
            json.dumps(
                {
                    "source": "uniswap",
                    "reason": "subgraph_errors",
                    "http_status": resp.status_code,
                    "has_data": False,
                    "elapsed_ms": elapsed_ms,
                    "body_sample": str(payload.get("errors"))[:200],
                }
            )
        )
        return {}

    return payload


# ---------------------------------------------------------------------------
# Public fetch helpers
# ---------------------------------------------------------------------------

async def fetch_positions(
    session: httpx.AsyncClient, owner: str, *, first: int = 100
) -> Optional[List[Dict[str, Any]]]:
    """Fetch all positions for ``owner``.

    Returns ``None`` on failure so callers can decide how to handle missing
    data.  Pagination via ``id_gt`` is supported transparently.
    """

    url = _subgraph_url()
    if not url:
        logger.warning(json.dumps({"source": "uniswap", "reason": "missing_url"}))
        return None

    all_positions: List[Dict[str, Any]] = []
    last_id: Optional[str] = None

    while True:
        try:
            payload = await graphql_query(
                session,
                url,
                POSITIONS_QUERY,
                {"owner": owner, "first": first, "lastId": last_id},
            )
        except Exception:
            return None

        positions, err = require_field(payload, ["data", "positions"])
        if positions is None:
            logger.warning(json.dumps({"source": "uniswap", "reason": err, "has_data": False}))
            return None

        all_positions.extend(positions)
        if len(positions) < first:
            break
        last_id = positions[-1]["id"]

    return all_positions


async def fetch_pool_state(
    session: httpx.AsyncClient, pool_id: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Fetch pool state for ``pool_id``.

    Returns ``None`` on failure or if ``pool_id`` is missing.
    """

    if not pool_id:
        return None

    url = _subgraph_url()
    if not url:
        logger.warning(json.dumps({"source": "uniswap", "reason": "missing_url"}))
        return None

    try:
        payload = await graphql_query(session, url, POOL_QUERY, {"poolId": pool_id})
    except Exception:
        return None

    pool, err = require_field(payload, ["data", "pool"])
    if pool is None:
        logger.warning(json.dumps({"source": "uniswap", "reason": err, "has_data": False}))
        return None
    return pool


# ---------------------------------------------------------------------------
# Amount and delta computations
# ---------------------------------------------------------------------------

def tick_to_sqrt_price(tick: int) -> float:
    return math.pow(1.0001, tick / 2)


def liquidity_to_amounts(
    liq: float, sqrt_p: float, sqrt_lower: float, sqrt_upper: float
) -> tuple[float, float]:
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


def _position_amounts(position: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Return token amounts for a position or ``None`` if unavailable."""

    pool = position.get("pool", {})
    sqrt_price_str = pool.get("sqrtPrice") or pool.get("sqrtPriceX96")
    liquidity = position.get("liquidity")
    tick_lower = position.get("tickLower", {}).get("tickIdx") or position.get("tickLower", {}).get("tick")
    tick_upper = position.get("tickUpper", {}).get("tickIdx") or position.get("tickUpper", {}).get("tick")

    if all(v is not None for v in (sqrt_price_str, liquidity, tick_lower, tick_upper)):
        try:
            sqrt_price = float(sqrt_price_str) / (1 << 96)
            sqrt_lower = tick_to_sqrt_price(int(tick_lower))
            sqrt_upper = tick_to_sqrt_price(int(tick_upper))
            return liquidity_to_amounts(float(liquidity), sqrt_price, sqrt_lower, sqrt_upper)
        except Exception:  # pragma: no cover - defensive
            return None

    # Fallback using deposited/withdrawn amounts (low precision)
    dep0 = float(position.get("depositedToken0") or 0)
    dep1 = float(position.get("depositedToken1") or 0)
    wd0 = float(position.get("withdrawnToken0") or 0)
    wd1 = float(position.get("withdrawnToken1") or 0)
    fee0 = float(position.get("collectedFeesToken0") or 0)
    fee1 = float(position.get("collectedFeesToken1") or 0)
    amt0 = dep0 - wd0 - fee0
    amt1 = dep1 - wd1 - fee1
    if amt0 == 0 and amt1 == 0:
        return None
    return amt0, amt1


def position_delta(position: Dict[str, Any]) -> float:
    """Return WETH exposure (positive if long WETH)."""

    amounts = _position_amounts(position)
    if amounts is None:
        raise ValueError("insufficient position data")

    pool = position.get("pool", {})
    sqrt_price_str = pool.get("sqrtPrice") or pool.get("sqrtPriceX96")
    if sqrt_price_str is None:
        raise ValueError("missing price")
    sqrt_price = float(sqrt_price_str) / (1 << 96)
    price = sqrt_price**2

    token0 = pool.get("token0", {}).get("symbol")
    token1 = pool.get("token1", {}).get("symbol")
    amt0, amt1 = amounts
    if token0 == "WETH" and token1 == "USDC":
        return amt0 - amt1 / price
    if token1 == "WETH" and token0 == "USDC":
        return amt1 - amt0 / price
    raise ValueError("unexpected token order")


def compute_lp_delta_safely(
    positions: Optional[List[Dict[str, Any]]], pool_state: Optional[Dict[str, Any]]
) -> Optional[float]:
    """Compute aggregate delta in WETH for a list of LP positions.

    Returns ``None`` if required data is missing.  Empty position lists
    produce a delta of ``0.0``.
    """

    if positions is None:
        return None
    if not positions:
        return 0.0

    pool = pool_state or positions[0].get("pool")
    if not pool:
        return None

    sqrt_price_str = pool.get("sqrtPrice") or pool.get("sqrtPriceX96")
    if sqrt_price_str is None:
        return None
    sqrt_price = float(sqrt_price_str) / (1 << 96)
    price = sqrt_price**2

    token0 = pool.get("token0", {}).get("symbol")
    token1 = pool.get("token1", {}).get("symbol")
    if not token0 or not token1:
        return None

    total0 = 0.0
    total1 = 0.0
    for pos in positions:
        amounts = _position_amounts(pos)
        if amounts is None:
            return None
        amt0, amt1 = amounts
        total0 += amt0
        total1 += amt1

    if token0 == "WETH" and token1 == "USDC":
        amt_weth, amt_usdc = total0, total1
    elif token1 == "WETH" and token0 == "USDC":
        amt_weth, amt_usdc = total1, total0
    else:
        return None

    return amt_weth - (amt_usdc / price)


def coerce_zero_if_none(x: Optional[float]) -> float:
    """Return ``0.0`` when ``x`` is ``None`` for safe printing/sums."""

    return 0.0 if x is None else x


__all__ = [
    "fetch_positions",
    "fetch_pool_state",
    "compute_lp_delta_safely",
    "coerce_zero_if_none",
    "position_delta",
]

