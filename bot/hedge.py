"""Hedge management."""
from __future__ import annotations

from .strategy import compute_strategy, StrategyResult
from .config import get_settings
from .executor import Executor


async def rebalance(executor: Executor, *, lp_delta: float, perp_position: float, price: float, margin: float, atr: float, funding_apr: float) -> StrategyResult:
    """Compute strategy and execute if needed."""
    result = compute_strategy(lp_delta, perp_position, price, margin, atr, funding_apr)
    if result.action == "adjust" and get_settings().MODE == "active":
        await executor.set_hedge(result.hedge_size)
    return result
