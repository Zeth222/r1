"""Execution layer for hedging trades."""
from __future__ import annotations

import time
import uuid
from typing import Optional

import httpx

from .config import get_settings
from .data.hyperliquid import place_order


class Executor:
    """Handles execution of perp hedge orders."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self._last_action = 0.0

    async def set_hedge(self, target: float) -> None:
        settings = get_settings()
        now = time.time()
        if now - self._last_action < settings.COOLDOWN_SEC:
            return
        self._last_action = now
        # For simplicity assume current position is fetched separately; we just submit order size=target
        side = "sell" if target < 0 else "buy"
        await place_order(self.client, symbol=settings.PAIR, size=abs(target), side=side)
