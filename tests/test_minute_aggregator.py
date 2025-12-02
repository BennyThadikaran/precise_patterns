import unittest
import unittest.mock
import helpers
from datetime import datetime, time, timedelta
from precise_patterns.candles.aggregator import MinuteAggregator

event_bus_module_path = "precise_patterns.candles.aggregator.event_bus"


class TestMinuteAggregator(unittest.TestCase):
    def setUp(self):
        """
        Prepare a fresh FakeBus and MinuteAggregator before every test.
        """
        self.fake_bus = helpers.FakeBus()
        self.start = time(9, 30)
        self.end = time(16, 0)
        self.agg = MinuteAggregator(self.start, self.end, filter_timeframes=[1, 3])

    def _ts(self, hour=9, minute=30):
        """Helper: build timestamps on a predictable date."""
        return datetime(2024, 1, 1, hour, minute)

    @unittest.mock.patch(event_bus_module_path)
    def test_first_minute_creates_and_updates_candle(
        self, mock_bus: unittest.mock.Mock
    ):
        """
        Test that the first 1-minute candle creates data and emits a 1-minute event immediately.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        ts = self._ts()
        self.agg.on_candle_close("AAPL", ts, 100, 101, 99, 100.5, 10)

        # 1-minute frame should emit once
        self.assertEqual(len(self.fake_bus.calls), 1)
        emitted = self.fake_bus.calls[0][0]
        self.assertEqual(emitted["timestamp"], ts)
        self.assertEqual(emitted["open"], 100)

    @unittest.mock.patch(event_bus_module_path)
    def test_candle_aggregates_until_tf_boundary(self, mock_bus: unittest.mock.Mock):
        """
        Ensure candles accumulate data until timeframe boundary (3 minutes) before emitting.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        base = self._ts()

        # 3 minutes of updates
        for i in range(3):
            self.agg.on_candle_close(
                "AAPL",
                base + timedelta(minutes=i),
                100 + i,
                101 + i,
                99 - i,
                100 + i,
                10,
            )

        # 1-min events emitted each minute
        self.assertEqual(len(self.fake_bus.calls), 3)

        # #4 execution triggers the 3-minute TF event
        self.agg.on_candle_close(
            "AAPL", base + timedelta(minutes=3), 110, 111, 109, 110, 15
        )
        # One more 1-min event + one 3-min event
        self.assertEqual(len(self.fake_bus.calls), 5)

    @unittest.mock.patch(event_bus_module_path)
    def test_session_start_resets_candle_builder(self, mock_bus: unittest.mock.Mock):
        """
        At exact session start, the internal CandleBuilders must reset timestamp.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        ts = self._ts(9, 30)
        self.agg.on_candle_close("AAPL", ts, 200, 205, 195, 202, 100)

        # A 1-minute candle emitted
        emitted = self.fake_bus.calls[0][0]
        self.assertEqual(emitted["timestamp"], ts)

        # Internal state timestamp must match session start
        builder = self.agg.data["AAPL"][3]
        self.assertEqual(builder.data["timestamp"], ts)

    @unittest.mock.patch(event_bus_module_path)
    def test_session_end_emits_all_timeframes_and_resets(
        self, mock_bus: unittest.mock.Mock
    ):
        """
        At end of session the aggregator emits both TFs and resets next day start.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        end_ts = datetime.combine(self._ts(), self.end) - timedelta(minutes=1)

        # Advance state by 1 candle THEN end‐session candle
        self.agg.on_candle_close("AAPL", self._ts(), 100, 101, 99, 100, 10)
        calls_before = len(self.fake_bus.calls)

        self.agg.on_candle_close("AAPL", end_ts, 110, 111, 109, 110, 15)

        # Should emit all TFs (1 and 3)
        calls_after = len(self.fake_bus.calls)
        self.assertGreater(calls_after, calls_before)

        # State should reset next stamp
        self.assertIsNone(self.agg.start_date)
        self.assertIsNone(self.agg.end_date)

    @unittest.mock.patch(event_bus_module_path)
    def test_new_day_resets_and_emits_all_tf(self, mock_bus: unittest.mock.Mock):
        """
        When timestamp exceeds session end, a new day starts and emits a close for all TF builders.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        next_day = datetime(2024, 1, 2, 9, 30)
        self.agg.on_candle_close("AAPL", self._ts(), 300, 310, 290, 305, 20)

        # Call close at next day → new session triggers full event flush
        self.agg.on_candle_close("AAPL", next_day, 300, 310, 290, 305, 20)

        # All TFs should be emitted: 1 and 3
        self.assertGreaterEqual(len(self.fake_bus.calls), 2)

    @unittest.mock.patch(event_bus_module_path)
    def test_ignored_timeframe_does_not_emit(self, mock_bus: unittest.mock.Mock):
        """
        If a timeframe is not included in filter_timeframes, it should never emit.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit
        agg = MinuteAggregator(self.start, self.end, filter_timeframes=[1])  # no 3-min

        ts = self._ts()
        for i in range(3):
            agg.on_candle_close(
                "AAPL", ts + timedelta(minutes=i), 100, 101, 99, 100, 10
            )

        # Only 1-minute events expected → 3 calls, none for 3-min TF
        self.assertEqual(len(self.fake_bus.calls), 3)


if __name__ == "__main__":
    unittest.main()
