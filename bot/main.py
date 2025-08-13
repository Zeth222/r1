"""Entrypoint for the hedge bot."""
from __future__ import annotations

import asyncio
import httpx

from .config import get_settings
from .logging_setup import setup_logging
from .notifier import Notifier
from .scheduler import create_scheduler, schedule_main_loop, schedule_reports
from .executor import Executor
from .hedge import rebalance
from .data import uniswap, hyperliquid, prices
from .reports import build_daily_report, build_weekly_report


async def main_loop(client: httpx.AsyncClient, notifier: Notifier, executor: Executor, oracle: prices.PriceOracle) -> None:
    settings = get_settings()
    try:
        positions = await uniswap.fetch_positions(client, settings.WALLET_ADDRESS)
        lp_delta = sum(uniswap.position_delta(p) for p in positions)
    except Exception as exc:  # pragma: no cover - external call
        await notifier.send_message(f"Uniswap fetch failed: {exc}", key="uniswap-error")
        return
    try:
        perp = await hyperliquid.fetch_positions(client, settings.WALLET_ADDRESS)
        perp_pos = float(perp.get("position", 0.0))
        margin = float(perp.get("margin", 0.0))
        funding_apr = float(perp.get("fundingApr", 0.0))
    except Exception as exc:  # pragma: no cover
        await notifier.send_message(f"Hyperliquid fetch failed: {exc}", key="hl-error")
        return
    price = await oracle.fetch_price(client, "ethereum")
    atr = oracle.atr()
    result = await rebalance(executor, lp_delta=lp_delta, perp_position=perp_pos, price=price, margin=margin, atr=atr, funding_apr=funding_apr)
    if result.action == "adjust":
        await notifier.send_message(f"Hedge adjusted to {result.hedge_size:.4f} WETH, lev {result.target_leverage:.2f}")


async def async_main() -> None:
    settings = get_settings()
    setup_logging()
    notifier = Notifier(settings.TELEGRAM_TOKEN or "", settings.TELEGRAM_CHAT_ID or "")
    oracle = prices.PriceOracle(settings.ATR_LOOKBACK_MIN)
    async with httpx.AsyncClient(timeout=10) as client:
        executor = Executor(client)
        scheduler = create_scheduler(settings.TZ)
        schedule_main_loop(scheduler, lambda: main_loop(client, notifier, executor, oracle), interval=5)
        schedule_reports(
            scheduler,
            lambda: notifier.send_report(build_daily_report()),
            lambda: notifier.send_report(build_weekly_report()),
            hour=settings.DAILY_REPORT_HOUR,
            dow=settings.WEEKLY_REPORT_DOW,
        )
        scheduler.start()
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(async_main())
