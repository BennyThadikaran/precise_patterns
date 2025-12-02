from abc import ABC, abstractmethod
from datetime import datetime


class BaseAggregator(ABC):
    """
    Abstract base class for candle aggregation logic.

    Concrete implementations must handle candle close events
    and emit new candles based on configured timeframes.

    :raises NotImplementedError: When subclass does not override
                                 :func:`on_candle_close`

    .. note::
       Aggregators emit events to the global ``event_bus`` under the
       channel ``"candle.close"``.

    .. seealso:: :class:`EODAggregator`, :class:`MinuteAggregator`

    """

    @abstractmethod
    def on_candle_close(
        self,
        symbol,
        ts: datetime,
        o: float,
        h: float,
        l: float,
        c: float,
        v: float,
    ) -> None:
        """Resample the candle to various EOD or minute timeframes"""
        pass
