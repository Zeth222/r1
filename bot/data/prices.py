"""Price utilities and indicators."""
from __future__ import annotations

from collections import deque
from typing import Deque, List

import httpx
import numpy as np


class PriceOracle:
    """Fetches prices and computes ATR."""

    def __init__(self, lookback: int = 60) -> None:
        self.lookback = lookback
        self.prices: Deque[float] = deque(maxlen=lookback)

    async def fetch_price(self, client: httpx.AsyncClient, symbol: str) -> float:
        # placeholder price feed
        resp = await client.get(f"https://api.coingecko.com/api/v3/simple/price", params={"ids": symbol, "vs_currencies": "usd"})
        resp.raise_for_status()
        price = resp.json()[symbol]["usd"]
        self.prices.append(price)
        return price

    def atr(self) -> float:
        if len(self.prices) < 2:
            return 0.0
        diffs = np.diff(np.array(self.prices))
        return float(np.mean(np.abs(diffs)))
