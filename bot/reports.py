"""Report generation for Telegram."""
from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import select, func

from .storage import SessionLocal, Snapshot, MetricsDaily


def build_daily_report() -> str:
    with SessionLocal() as session:
        today = datetime.utcnow().date()
        pnl = session.get(MetricsDaily, str(today))
        if pnl:
            net = pnl.net_pnl
        else:
            net = 0.0
    return f"Daily PnL: {net:.2f} USD"


def build_weekly_report() -> str:
    return "Weekly report placeholder"
