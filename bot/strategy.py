"""Strategy logic for dynamic hedge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .config import get_settings
from . import risk


@dataclass
class StrategyResult:
    hedge_size: float
    target_leverage: float
    action: str  # "adjust", "hold", "remove"


def compute_strategy(lp_delta: float, perp_position: float, price: float, margin: float, atr: float, funding_apr: float) -> StrategyResult:
    """Compute hedge target and leverage based on current state."""
    s = get_settings()
    exposure = lp_delta
    target_perp = -exposure
    delta = target_perp - perp_position
    action = "adjust" if abs(delta) > s.DELTA_TOLERANCE_PCT * abs(exposure) else "hold"
    lev = risk.target_leverage(exposure, margin, price, atr, funding_apr)
    return StrategyResult(hedge_size=target_perp, target_leverage=lev, action=action)
