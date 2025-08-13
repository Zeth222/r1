"""Telegram notifications."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from telegram import Bot


class Notifier:
    """Simple Telegram notifier with basic anti-spam."""

    def __init__(self, token: str, chat_id: str) -> None:
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self._last_sent: dict[str, datetime] = defaultdict(lambda: datetime.min)
        self._debounce = timedelta(seconds=60)
        self._once_sent: dict[str, datetime] = defaultdict(lambda: datetime.min)
        self._once_debounce = timedelta(minutes=15)

    async def send_message(self, text: str, *, key: str = "generic") -> None:
        now = datetime.utcnow()
        if now - self._last_sent[key] < self._debounce:
            return
        self._last_sent[key] = now
        await self.bot.send_message(chat_id=self.chat_id, text=text)

    async def once(self, key: str, text: str) -> None:
        """Send ``text`` once per ``key`` with a long debounce."""

        now = datetime.utcnow()
        if now - self._once_sent[key] < self._once_debounce:
            return
        self._once_sent[key] = now
        await self.bot.send_message(chat_id=self.chat_id, text=text)

    async def send_report(self, text: str) -> None:
        await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode="Markdown")
