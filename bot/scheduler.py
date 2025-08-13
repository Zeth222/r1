"""Scheduler setup using APScheduler."""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Any, Awaitable, Callable
import asyncio


def create_scheduler(tz: str) -> AsyncIOScheduler:
    """Create scheduler with timezone."""
    return AsyncIOScheduler(timezone=tz)


def schedule_main_loop(
    scheduler: AsyncIOScheduler,
    func: Callable[..., Awaitable[None]],
    *,
    args: tuple[Any, ...] = (),
    interval: int = 5,
) -> None:
    """Schedule main loop job."""

    async def job() -> None:
        await func(*args)

    scheduler.add_job(job, "interval", seconds=interval, id="main-loop", replace_existing=True)


def schedule_reports(
    scheduler: AsyncIOScheduler,
    daily: Callable[[], Awaitable[None]],
    weekly: Callable[[], Awaitable[None]],
    *,
    hour: int,
    dow: int,
) -> None:
    """Schedule daily and weekly report jobs."""

    scheduler.add_job(lambda: asyncio.create_task(daily()), CronTrigger(hour=hour))
    normalized_dow = dow % 7
    scheduler.add_job(
        lambda: asyncio.create_task(weekly()),
        CronTrigger(day_of_week=normalized_dow, hour=hour),
    )
