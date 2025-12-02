import context
from typing import List, Deque
from precise_patterns.dtypes import Pivot, Candle
from datetime import datetime


class FakeBus:
    """
    Mock class to imitate event_bus

    Used to capture and store Pivot Dicts when `pivot.confirm` event is emitted.
    """

    def __init__(self):
        self.calls = []

    def emit(self, event: str, *args):
        self.calls.append(args)


def candle(high: float, low: float, ts: datetime) -> Candle:
    """Helper function to generate Candle Dicts"""
    return Candle(
        symbol="FOO",
        timeframe="D",
        timestamp=ts,
        open=100,
        high=high,
        low=low,
        close=100,
        volume=1000,
    )


def is_monotonic_decreasing(lst: Deque[Candle]) -> bool:
    """Test if candle highs are in descending order"""
    return all([lst[i]["high"] >= lst[i + 1]["high"] for i in range(len(lst) - 1)])


def is_monotonic_increasing(lst: Deque[Candle]) -> bool:
    """test if candle lows are in ascending order"""
    return all([lst[i]["low"] <= lst[i + 1]["low"] for i in range(len(lst) - 1)])
