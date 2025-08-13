"""Risk management helpers."""
from __future__ import annotations

from .config import get_settings


def target_leverage(exposure: float, margin: float, price: float, atr: float, funding_apr: float) -> float:
    """Compute target hedge leverage given exposure and risk params."""
    s = get_settings()
    mreq = abs(exposure) / s.HEDGE_LEVERAGE_TARGET
    buffer = mreq * (1 + s.MIN_MARGIN_BUFFER_PCT + atr / price)
    lev = abs(exposure) / max(mreq + buffer, 1e-8)
    lev = max(1.5, min(3.0, lev))
    if funding_apr > s.FUNDING_ALERT_PCT:
        lev = min(lev, 2.0)
    return lev


def kill_switch(delta: float, notional_lp: float, margin_ratio: float) -> bool:
    """Return True if hedge should be unwound due to risk limits."""
    s = get_settings()
    if abs(delta) > 3 * s.DELTA_TOLERANCE_PCT * notional_lp:
        return True
    if margin_ratio < (1 + s.MIN_MARGIN_BUFFER_PCT):
        return True
    return False
