from .base.aggregator import BaseAggregator
from datetime import datetime, time, date, timedelta
from .dtypes import OHLC, Candle, EODTimeframes
from typing import List, Dict, Set
from .events import event_bus
from math import inf


class CandleBuilder:
    """
    Builds and updates OHLC candle data.

    A :class:`~.CandleBuilder` instance accumulates OHLC data from 1 minute or daily candles
    until a candle timeframe completes. It maintains an internal OHLCV structure
    using :class:`dict` fields compatible with :class:`~.OHLC`.

    :param ts: Initial timestamp of the candle
    :type ts: :class:`~datetime.datetime`
    :param o: Opening price
    :type o: :class:`float`
    :param h: Highest price encountered
    :type h: :class:`float`
    :param l: Lowest price encountered
    :type l: :class:`float`
    :param c: Closing price
    :type c: :class:`float`
    :param v: Trading volume
    :type v: :class:`float`

    :ivar data: Mutable OHLC data being accumulated
    :vartype data: :class:`~.OHLC`

    .. seealso:: :class:`~.BaseAggregator`
    """

    def __init__(
        self, ts: datetime, o: float, h: float, l: float, c: float, v: float
    ) -> None:
        self.data = OHLC(timestamp=ts, open=o, high=h, low=l, close=c, volume=v)

    def update(self, o: float, h: float, l: float, c: float, v: float):
        """
        Update the current OHLC candle values.

        :param o: Latest open price
        :type o: :class:`float`
        :param h: Latest high price
        :type h: :class:`float`
        :param l: Latest low price
        :type l: :class:`float`
        :param c: Latest close price
        :type c: :class:`float`
        :param v: Additional traded volume
        :type v: :class:`float`
        """
        if not self.data["open"]:
            self.data["open"] = o

        if h > self.data["high"]:
            self.data["high"] = h

        if l < self.data["low"]:
            self.data["low"] = l

        self.data["close"] = c
        self.data["volume"] += v

    def reset(self, ts: datetime):
        """
        Reset internal candle state to a new timestamp.

        :param ts: New base timestamp for candle accumulation
        :type ts: :class:`~datetime.datetime`

        .. warning::
           All OHLC values will be cleared and volume reset to zero.
        """
        self.data["timestamp"] = ts

        self.data["open"] = 0
        self.data["high"] = -inf
        self.data["low"] = inf
        self.data["close"] = 0
        self.data["volume"] = 0


class EODAggregator(BaseAggregator):
    """
    Aggregates daily candles into :class:`~precise_patterns.dtypes.EODTimeframes`.

    This includes daily (``"D"``), weekly (``"W"``), monthly (``"M"``), and
    quarterly (``"Q"``) timeframes. Handles exchange holidays, alternative
    sessions, and varying "last weekday" settlement rules.

    :param filter_timeframes: Set of EOD timeframes to emit. Defaults to :class:`~precise_patterns.dtypes.EODTimeframes`
    :type filter_timeframes: :class:`list` of :class:`~precise_patterns.dtypes.EODTimeframes` or ``None``
    :param last_weekday: The last valid trading weekday (0=Mon,…,6=Sun), default is 5 (Saturday)
    :type last_weekday: :class:`int`
    :param holidays: Non-trading days to skip when calculating week/month ends
    :type holidays: :class:`list` of :class:`datetime.date`
    :param extra_sessions: Additional trading days treated as valid sessions
    :type extra_sessions: :class:`list` of :class:`datetime.date`

    :ivar filter_timeframes: Enabled timeframes
    :vartype filter_timeframes: :class:`set` of :class:`~precise_patterns.dtypes.EODTimeframes`
    :ivar data: A dict holding CandleBuilder instaces per symbol and timeframe
    :vartype data: :class:`Dict`\\[:class:`str`, :class:`Dict`\\[:class:`~precise_patterns.dtypes.EODTimeframes`, :class:`~.CandleBuilder`]\\]

    :raises ValueError: If ``holidays`` or ``extra_sessions`` contain non-date types

    .. note::
       This emits the ``"candle.close"`` event with payload type:
       :class:`~precise_patterns.dtypes.Candle`

    .. note::
       The daily timeframe is always emitted directly without aggregation
       if present in ``filter_timeframes``.

    .. seealso::
       :class:`MinuteAggregator`
       :func:`get_weekend`
       :func:`get_monthend`
       :func:`get_quarter_end`
    """

    def __init__(
        self,
        filter_timeframes: List[EODTimeframes] | None = None,
        last_weekday: int = 5,
        holidays: List[date] = [],
        extra_sessions: List[date] = [],
    ) -> None:
        self.filter_timeframes: Set[EODTimeframes] = (
            set(filter_timeframes) if filter_timeframes else set(["D", "W", "M", "Q"])
        )

        if not all(type(dt) is date for dt in holidays):
            raise ValueError("holidays must be a list of datetime.date instances")

        if not all(type(dt) is date for dt in extra_sessions):
            raise ValueError("extra_sessions must be a list of datetime.date instances")

        self.holidays = set(holidays)
        self.extra_sessions = set(extra_sessions)

        self.last_weekday = last_weekday

        self.quarter_end_date = None
        self.monthend_date = None
        self.weekend_date = None

        self.tf_closed = []
        self.data: Dict[str, Dict[EODTimeframes, CandleBuilder]] = {}

    def get_quarter_end(self, dt: date) -> date:
        """
        Compute the last trading date of the quarter for the given date.

        :param dt: Reference date within the desired quarter
        :type dt: :class:`datetime.date`
        :return: Calculated quarter end date
        :rtype: :class:`datetime.date`

        .. seealso:: :func:`get_monthend`
        """
        # zero indexed quarter number.
        # 1st Quarter is 0, 2nd quarter is 1
        q = (dt.month - 1) // 3  # k

        # Get the quarter end month 3, 6, 9, 12
        month = (q + 1) * 3

        return self.get_monthend(date(dt.year, month, 1))

    def get_monthend(self, dt: date) -> date:
        """
        Determine the last valid trading date of the month.

        Handles weekends, holidays, and extra sessions as configured.

        :param dt: A date within the target month
        :type dt: :class:`datetime.date`
        :return: Adjusted month-end trading date
        :rtype: :class:`datetime.date`
        """
        # last day of month = 1st day of next month - 1 day
        next_month = dt.month + 1
        year = dt.year

        if next_month > 12:
            next_month = 1
            year += 1

        dt = date(year=year, month=next_month, day=1) - timedelta(days=1)

        if self.last_weekday == 5:
            return dt

        # adjust backwards for market holidays and weekends
        while True:
            if dt.weekday() > self.last_weekday:
                dt = dt - timedelta(1)
                continue

            if self.holidays and dt in self.holidays:
                dt = dt - timedelta(1)
                continue
            break

        for session_dt in self.extra_sessions:
            if session_dt.month == dt.month:
                return session_dt if session_dt > dt else dt

        return dt

    def get_weekend(self, dt: date) -> date:
        """
        Compute the last valid trading day of the week.

        Considers holidays, weekend rules, and designated extra sessions.

        :param dt: Date used to find corresponding week end
        :type dt: :class:`datetime.date`
        :return: Date when weekly candle should close
        :rtype: :class:`datetime.date`
        """

        weekday = dt.weekday()

        # Saturday always marks the week end
        if weekday == 5:
            return dt

        saturday_dt = dt + timedelta(5 - weekday)

        days_to_weekend = self.last_weekday - weekday

        # special case Sunday being 6, results in negative value
        if days_to_weekend < 0:
            days_to_weekend = self.last_weekday + 1

        dt = dt + timedelta(days_to_weekend)

        if self.holidays:
            # Go a day back if current date is a holiday
            while True:
                if dt in self.holidays:
                    dt = dt - timedelta(1)
                    continue
                break

        if self.extra_sessions:
            # If any extra session extend the week and return the last one
            for session in self.extra_sessions:
                if session <= saturday_dt and session >= dt:
                    return session

        return dt

    def emit_event(self, symbol, tf):
        """
        Emit a candle event to the event bus.

        :param symbol: Asset symbol
        :type symbol: :class:`str`
        :param tf: Timeframe key ("D", "W", "M", "Q")
        :type tf: :class:`~precise_patterns.dtypes.EODTimeframes`.

        .. note::
           Uses ``"candle.close"`` event channel.
        """
        event_bus.emit(
            "candle.close",
            Candle(
                symbol=symbol,
                timeframe=tf,
                **self.data[symbol][tf].data,
            ),
        )

    def on_candle_close(
        self, symbol, ts: datetime, o: float, h: float, l: float, c: float, v: float
    ):
        """
        Process a closed daily candle into higher timeframes.

        Uses :class:~.CandleBuilder to accumulate OHLCV values,
        checks period boundaries, and emits completed candles
        for the configured EOD timeframes.

        :param symbol: Market symbol
        :type symbol: :class:`str`
        :param ts: Candle timestamp
        :type ts: :class:`~datetime.datetime`
        :param o: Open price
        :type o: :class:`float`
        :param h: High price
        :type h: :class:`float`
        :param l: Low price
        :type l: :class:`float`
        :param c: Close price
        :type c: :class:`float`
        :param v: Volume
        :type v: :class:`float`
        """
        if "D" in self.filter_timeframes:
            event_bus.emit(
                "candle.close",
                Candle(
                    symbol=symbol,
                    timeframe="D",
                    timestamp=ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=v,
                ),
            )

        dt = ts.date()

        if self.quarter_end_date and dt > self.quarter_end_date:
            if "Q" in self.filter_timeframes:
                self.emit_event(symbol, "Q")

                self.data[symbol]["Q"].reset(ts)

                self.quarter_end_date = None

        if self.monthend_date and dt > self.monthend_date:
            if "M" in self.filter_timeframes:
                self.emit_event(symbol, "M")

                self.data[symbol]["M"].reset(ts)

                self.monthend_date = None

        if self.weekend_date and dt > self.weekend_date:
            if "W" in self.filter_timeframes:
                self.emit_event(symbol, "W")

                self.data[symbol]["W"].reset(ts)

                self.weekend_date = None

        if not self.quarter_end_date:
            self.quarter_end_date = self.get_quarter_end(dt)

        if not self.monthend_date:
            self.monthend_date = self.get_monthend(dt)

        if not self.weekend_date:
            self.weekend_date = self.get_weekend(dt)

        for tf in self.filter_timeframes:
            if symbol not in self.data:
                self.data[symbol] = {}

            if tf in self.data[symbol]:
                self.data[symbol][tf].update(o, h, l, c, v)
            else:
                self.data[symbol][tf] = CandleBuilder(ts, o, h, l, c, v)

        if dt == self.weekend_date:
            if "W" in self.filter_timeframes:
                self.emit_event(symbol, "W")

                self.data[symbol]["W"].reset(ts)

                self.weekend_date = None

        if dt == self.monthend_date:
            if "M" in self.filter_timeframes:
                self.emit_event(symbol, "M")

                self.data[symbol]["M"].reset(ts)

                self.monthend_date = None

        if dt == self.quarter_end_date:
            if "Q" in self.filter_timeframes:
                self.emit_event(symbol, "Q")

                self.data[symbol]["Q"].reset(ts)

                self.quarter_end_date = None


class MinuteAggregator(BaseAggregator):
    """
    Aggregates 1-minute candles into multiple intraday minute timeframes.

    Resets and reinitializes session boundaries at the start of each trading
    day, ensuring time-based aggregation remains aligned to intraday sessions.

    :param start_time: Session start time (included)
    :type start_time: :class:`datetime.time`
    :param end_time: Session end time (included)
    :type end_time: :class:`datetime.time`
    :param filter_timeframes: Minute-based aggregation intervals (e.g. 3, 5, 15).
                              Defaults to a common set.
    :type filter_timeframes: :class:`list` of :class:`int` or ``None``

    :ivar data: Accumulated per-symbol intraday compression state
    :vartype data: :class:`dict`
    :ivar start_date: Expected session start timestamp for current day
    :vartype start_date: :class:`~datetime.datetime` or ``None``
    :ivar end_date: Expected session end timestamp for current day
    :vartype end_date: :class:`~datetime.datetime` or ``None``

    .. note::
       The 1-minute timeframe is always emitted directly without aggregation
       if present in ``filter_timeframes``.

    .. note::
       This emits the ``"candle.close"`` event with payload type:
       :class:`~precise_patterns.dtypes.Candle`

    .. seealso::
       :class:`EODAggregator`
       :class:`~.CandleBuilder`
    """

    def __init__(
        self,
        start_time: time,
        end_time: time,
        filter_timeframes: List[int] | None = None,
    ) -> None:
        self.filter_timeframes = (
            set(filter_timeframes)
            if filter_timeframes
            else set([3, 5, 15, 25, 30, 60, 75, 120, 125, 240])
        )

        self.start_time = start_time

        self.end_time = (
            datetime.combine(datetime.now(), time=end_time) - timedelta(minutes=1)
        ).time()

        self.data: Dict[str, Dict[int, CandleBuilder]] = {}

        self.count = 0
        self.start_date = self.end_date = None

    def emit_event(self, symbol: str, tf: int):
        """
        Emit a minute-based aggregated candle.

        :param symbol: Asset symbol
        :type symbol: :class:`str`
        :param tf: Minute timeframe value (e.g. 5, 15, 30)
        :type tf: :class:`int`
        """
        event_bus.emit(
            "candle.close",
            Candle(
                symbol=symbol,
                timeframe=tf,
                **self.data[symbol][tf].data,
            ),
        )

    def on_candle_close(
        self,
        symbol: str,
        ts: datetime,
        o: float,
        h: float,
        l: float,
        c: float,
        v: float,
    ):
        """
        Aggregate 1-minute candles into configured minute timeframes.

        Maintains session-aware boundaries, flushing data when the session
        ends or timeframe is complete.

        :param symbol: Symbol of the asset
        :type symbol: :class:`str`
        :param ts: Timestamp of the closing 1-minute candle
        :type ts: :class:`~datetime.datetime`
        :param o: Open price
        :type o: :class:`float`
        :param h: Highest price seen
        :type h: :class:`float`
        :param l: Lowest price seen
        :type l: :class:`float`
        :param c: Close price
        :type c: :class:`float`
        :param v: Volume
        :type v: :class:`float`

        .. note::
           Directly emits 1-minute candles if timeframe ``1`` enabled.
        """
        if 1 in self.filter_timeframes:
            event_bus.emit(
                "candle.close",
                Candle(
                    symbol=symbol,
                    timeframe=1,
                    timestamp=ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=v,
                ),
            )

        if not self.start_date or not self.end_date:
            self.start_date = datetime.combine(ts, self.start_time)
            self.end_date = datetime.combine(ts, self.end_time)

        if ts > self.end_date:
            self.start_date = datetime.combine(ts, self.start_time)
            self.end_date = datetime.combine(ts, self.end_time)

            for tf in self.filter_timeframes:
                if tf == 1:
                    continue
                self.emit_event(symbol, tf)
                self.data[symbol][tf].reset(ts)

        minutes_elapsed = (ts - self.start_date).seconds // 60

        is_session_start = ts == self.start_date
        is_session_end = ts == self.end_date

        if is_session_end:
            self.start_date = self.end_date = None

        for tf in self.filter_timeframes:
            if tf == 1:
                continue

            if minutes_elapsed and minutes_elapsed % tf == 0:
                self.emit_event(symbol, tf)
                self.data[symbol][tf].reset(ts)

            if symbol not in self.data:
                self.data[symbol] = {}

            if tf in self.data[symbol]:
                self.data[symbol][tf].update(o, h, l, c, v)
            else:
                self.data[symbol][tf] = CandleBuilder(ts, o, h, l, c, v)

            if is_session_start:
                self.data[symbol][tf].reset(ts)

            if is_session_end:
                self.emit_event(symbol, tf)
