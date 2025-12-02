from typing import Literal, TypedDict
from datetime import datetime


class OHLC(TypedDict):
    """
    A TypedDict representing a single OHLCV (Open–High–Low–Close–Volume) candle.

    :key datetime timestamp:
        The timestamp of the candle. Typically represents the open time of the period.

    :key float open:
        The opening price for the period.

    :key float high:
        The highest traded price during the period.

    :key float low:
        The lowest traded price during the period.

    :key float close:
        The closing price for the period.

    :key float volume:
        The traded volume during the period.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


EODTimeframes = Literal["D", "W", "M", "Q"]
"""Valid end-of-day timeframe identifiers.

:class:`str` literal type with allowed values:

- ``"D"`` — Daily
- ``"W"`` — Weekly
- ``"M"`` — Monthly
- ``"Q"`` — Quarterly
"""


class Candle(TypedDict):
    """
    Represents a single OHLCV (Open, High, Low, Close, Volume) candle
    with symbol and timeframe info.

    :key symbol: (str) Trading symbol or instrument identifier.
    :key timeframe: (EODTimeframes or int) Can be either an end-of-day
                    timeframe literal (``"D"``, ``"W"``, ``"M"``, ``"Q"``)
                    or an integer indicating a minute-based interval.
    :key timestamp: (datetime.datetime) Candle timestamp
    :key open: (float) Opening price.
    :key high: (float) Highest price reached during the candle.
    :key low: (float) Lowest price reached during the candle.
    :key close: (float) Closing price.
    :key volume: (float) Total traded volume within the candle.
    """

    symbol: str
    timeframe: EODTimeframes | int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Pivot(TypedDict):
    """
    Represents a confirmed pivot point (high or low) in the price series.

    :key symbol: (str) Trading symbol or instrument identifier.
    :key type: (Literal["high", "low"])
        Type of pivot detected — ``"high"`` for a local top, ``"low"`` for a local bottom.
    :key timeframe: (EODTimeframes or int) Time interval in which the pivot occurred.
                    Either an end-of-day timeframe literal (``"D"``, ``"W"``, ``"M"``,
                    ``"Q"``) or an integer indicating a minute-based interval.
    :key timestamp: (datetime.datetime) Timestamp of the pivot candle.
    :key price: (float) Price at which the pivot occurred.
    :key volume: (float) Volume associated with the pivot candle.
    """

    symbol: str
    type: Literal["high", "low"]
    timeframe: EODTimeframes | int
    timestamp: datetime
    price: float
    volume: float
