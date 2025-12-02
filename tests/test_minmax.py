import context
import helpers
import unittest
import unittest.mock
from datetime import datetime, timedelta
from precise_patterns.pivots import MinMax


class TestMinMax(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_bus = helpers.FakeBus()

    @unittest.mock.patch("precise_patterns.pivots.event_bus")
    def test_major_pivot_high_detected(self, mock_bus: unittest.mock.Mock):
        """Test is a pivot high is detected"""
        mock_bus.emit.side_effect = self.fake_bus.emit

        pivot = MinMax(length=7, pivot_pos=3)

        data = [[80, 70], [85, 70], [90, 70], [95, 70], [90, 70], [85, 70], [80, 70]]

        dt = datetime(2025, 1, 1)

        for ohlc in data:
            high, low = ohlc
            dt = dt + timedelta(1)
            pivot.update(helpers.candle(high, low, dt))

        self.assertEqual(len(self.fake_bus.calls), 1)
        self.assertEqual(self.fake_bus.calls[0][0]["price"], 95)
        self.assertEqual(self.fake_bus.calls[0][0]["type"], "high")

    @unittest.mock.patch("precise_patterns.pivots.event_bus")
    def test_major_pivot_low_detected(self, mock_bus):
        mock_bus.emit.side_effect = self.fake_bus.emit

        pivot = MinMax(length=7, pivot_pos=3)

        data = [[90, 98], [88, 96], [86, 94], [84, 92], [86, 94], [88, 96], [90, 98]]

        dt = datetime(2025, 1, 1)

        for high, low in data:
            dt = dt + timedelta(1)
            pivot.update(helpers.candle(high, low, dt))

        self.assertEqual(len(self.fake_bus.calls), 1)
        self.assertEqual(self.fake_bus.calls[0][0]["price"], 92)
        self.assertEqual(self.fake_bus.calls[0][0]["type"], "low")

    def test_minmax_buffer_behaviour(self):
        """
        With the max buffer length set to 7 and equivalent candles input,

        1. Test that no candles have been removed until full
        2. Insertion order of candles have been maintained
        3. Once full, adding a new candle removes the oldest
        """
        pivot = MinMax(length=7, pivot_pos=3)

        data = [[65, 50], [70, 50], [75, 50], [70, 50], [65, 50]]

        dt = datetime(2025, 1, 1)
        first_candle = helpers.candle(60, 50, dt)

        pivot.update(first_candle)

        for high, low in data:
            dt = dt + timedelta(1)
            pivot.update(helpers.candle(high, low, dt))

        dt = dt + timedelta(1)

        last_candle = helpers.candle(60, 50, dt)
        pivot.update(last_candle)

        self.assertEqual(len(pivot.buffer), pivot.buffer_length)
        self.assertTrue(pivot.buffer[0] is first_candle)
        self.assertTrue(pivot.buffer[-1] is last_candle)

        pivot.update(helpers.candle(96, 92, dt + timedelta(1)))
        self.assertFalse(pivot.buffer[0] is first_candle)

    def test_monotonic_behavior(self):
        """
        Test the monotonic behaviour of max and min deques in MinMax

        Entries in max deque are orders highest to lowest
        Entries in min deque are ordered lowest to highest
        """
        high = 2000
        low = 1950
        is_bullish = True
        pivot = MinMax(length=7, pivot_pos=3)
        dt = datetime(2025, 1, 1)

        # Simulate uptrend with higher high and higher lows
        for i in range(1, 1000):
            # change trend direction every 4 candles
            if i % 4 == 0:
                is_bullish = not is_bullish

            high = high + 10 if is_bullish else high - 5
            low = low + 5 if is_bullish else low - 15

            pivot.update(helpers.candle(high, low, dt))

            if len(pivot.max) > 1:
                self.assertTrue(helpers.is_monotonic_decreasing(pivot.max))

            if len(pivot.min) > 1:
                self.assertTrue(helpers.is_monotonic_increasing(pivot.min))


if __name__ == "__main__":
    unittest.main()
