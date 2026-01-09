from collections import deque
from typing import Deque, Dict
from .dtypes import Candle, Pivot, EODTimeframes
from .events import event_bus
from .base.pivot import BasePivotDetector


class MinMax:
    """
    A rolling-window min/max tracker used to detect high and low pivots

    This class is not directly instantiated but used by :class:`PivotDetector` class

    See https://www.nayuki.io/page/sliding-window-minimum-maximum-algorithm
    for explanation of algorithm.

    This class maintains a fixed-length deque of candles and two monotonic
    (consistently increasing or decreasing) deques for efficiently tracking
    the rolling minimum and maximum values.

    When the buffer reaches full length, the candle at the configured
    ``pivot_pos`` is evaluated to determine whether it forms a confirmed
    high or low pivot. If so, a ``pivot.confirm`` event is emitted through
    the global :mod:`event_bus`.

    :param int length:
        Total number of candles to maintain in the rolling window.
    :param int pivot_pos:
        Index of the pivot candle within the buffer.

    **Attributes**
        .. attribute:: buffer_length

           The fixed size of the rolling buffer.

        .. attribute:: pivot_pos

           The index of the potential pivot candle.

        .. attribute:: buffer

           A ``deque`` storing the most recent candles.

        .. attribute:: min

           A monotonic deque maintaining rolling minimum candle lows.

        .. attribute:: max

           A monotonic deque maintaining rolling maximum candle highs.
    """

    def __init__(self, length: int, pivot_pos: int) -> None:
        self.buffer_length = length
        self.pivot_pos = pivot_pos
        self.buffer: Deque[Candle] = deque(maxlen=self.buffer_length)
        self.min: Deque[Candle] = deque()
        self.max: Deque[Candle] = deque()

    def update(self, candle: Candle):
        """
        Update the rolling window with a new candle, maintain the monotonic
        min/max structures, and emit pivot events when a pivot is confirmed.

        :param Candle candle:
            The incoming candle to process.

        :return None: A ``pivot.confirm`` event may be emitted as a side effect.
        """
        buffer_full = len(self.buffer) == self.buffer_length

        if buffer_full:
            outgoing = self.buffer[0]

            if self.max and self.max[0] is outgoing:
                self.max.popleft()

            if self.min and self.min[0] is outgoing:
                self.min.popleft()

        self.buffer.append(candle)

        while self.max and candle["high"] >= self.max[-1]["high"]:
            self.max.pop()
        self.max.append(candle)

        while self.min and candle["low"] <= self.min[-1]["low"]:
            self.min.pop()
        self.min.append(candle)

        if len(self.buffer) < self.buffer_length:
            return

        pivot_candle = self.buffer[self.pivot_pos]

        if self.max and self.max[0] is pivot_candle:
            event_bus.emit(
                "pivot.confirm",
                Pivot(
                    symbol=pivot_candle["symbol"],
                    type="high",
                    timeframe=pivot_candle["timeframe"],
                    timestamp=pivot_candle["timestamp"],
                    price=pivot_candle["high"],
                    volume=pivot_candle["volume"],
                ),
                candle,
            )

        if self.min and self.min[0] is pivot_candle:
            event_bus.emit(
                "pivot.confirm",
                Pivot(
                    symbol=pivot_candle["symbol"],
                    type="low",
                    timeframe=pivot_candle["timeframe"],
                    timestamp=pivot_candle["timestamp"],
                    price=pivot_candle["low"],
                    volume=pivot_candle["volume"],
                ),
                candle,
            )


class PivotDetector(BasePivotDetector):
    """
    Detects pivot highs and lows using a configurable number of left and right bars.

    It creates and manages :class:`MinMax` instance for each
    symbol and timeframe. A pivot is confirmed when the candle at the pivot
    position is either the highest high or lowest low within the full
    rolling buffer.

    :param int left_bars:
        Number of candles to the *left* of the pivot candle. Must be greater
        than 0
    :param int right_bars:
        Number of candles to the *right* of the pivot candle. Must be greater than 0

    :raises ValueError:
        If ``left_bars`` or ``right_bars`` is 0

    **Attributes**
        .. attribute:: buffer_length

           Size of the rolling candle window, computed as
           ``left_bars + right_bars + 1``.

        .. attribute:: buffer

           Nested mapping of ``symbol -> timeframe -> MinMax`` instances,
           each maintaining its own rolling min/max evaluation.

        .. attribute:: pivot_pos

           Position of the pivot candle within each rolling window,
           equal to ``left_bars``.
    """

    def __init__(self, left_bars=6, right_bars=6) -> None:
        super().__init__()

        self.buffer_length = left_bars + 1 + right_bars
        self.pivot_pos = left_bars

        self.buffer: Dict[str, Dict[EODTimeframes | int, MinMax]] = {}

    def on_candle_close(self, candle: Candle) -> None:
        """
        Process a newly closed candle. If the corresponding
        ``(symbol, timeframe)`` does not yet exist, it is
        created. The candle is then forwarded to the underlying
        :class:`MinMax` instance for pivot evaluation.

        :param Candle candle:
            The closed candle that should be analyzed for potential pivot
            formation.

        :returns:
            ``None``. Validation and pivot detection occur internally and
            may emit a ``pivot.confirm`` events.
        """

        sym = candle["symbol"]
        tf = candle["timeframe"]

        if sym not in self.buffer:
            self.buffer[sym] = {}

        if tf not in self.buffer[sym]:
            self.buffer[sym][tf] = MinMax(
                length=self.buffer_length,
                pivot_pos=self.pivot_pos,
            )

        self.buffer[sym][tf].update(candle)
