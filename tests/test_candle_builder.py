import context
import unittest
from datetime import datetime, timedelta
from precise_patterns.candles.aggregator import CandleBuilder
from math import inf


class TestCandleBuilder(unittest.TestCase):
    def setUp(self):
        self.ts = datetime(2024, 1, 1, 12, 0, 0)
        self.cb = CandleBuilder(
            ts=self.ts,
            o=100.0,
            h=110.0,
            l=90.0,
            c=105.0,
            v=10.0,
        )

    def test_initialization(self):
        """Verify constructor initializes all OHLC fields correctly."""
        data = self.cb.data
        self.assertEqual(data["timestamp"], self.ts)
        self.assertEqual(data["open"], 100.0)
        self.assertEqual(data["high"], 110.0)
        self.assertEqual(data["low"], 90.0)
        self.assertEqual(data["close"], 105.0)
        self.assertEqual(data["volume"], 10.0)

    def test_update_values(self):
        """Ensure update correctly modifies high, low, close, and accumulates volume."""
        self.cb.update(o=120.0, h=120.0, l=85.0, c=115.0, v=5.0)
        data = self.cb.data

        # open should remain unchanged, since it's already set
        self.assertEqual(data["open"], 100.0)

        # high should increase
        self.assertEqual(data["high"], 120.0)

        # low should decrease
        self.assertEqual(data["low"], 85.0)

        # close always updates
        self.assertEqual(data["close"], 115.0)

        # volume should accumulate
        self.assertEqual(data["volume"], 15.0)

    def test_update_when_open_is_zero(self):
        """If open==0, update should set the open price."""
        ts = datetime(2024, 1, 2)
        cb = CandleBuilder(ts, o=0, h=-inf, l=inf, c=0, v=0)

        cb.update(o=50.0, h=51.0, l=49.0, c=50.5, v=3.0)
        data = cb.data

        self.assertEqual(data["open"], 50.0)
        self.assertEqual(data["high"], 51.0)
        self.assertEqual(data["low"], 49.0)
        self.assertEqual(data["close"], 50.5)
        self.assertEqual(data["volume"], 3.0)

    def test_reset(self):
        """Reset should zero/inf the correct fields and update timestamp."""
        new_ts = self.ts + timedelta(minutes=1)
        self.cb.reset(new_ts)
        data = self.cb.data

        self.assertEqual(data["timestamp"], new_ts)
        self.assertEqual(data["open"], 0)
        self.assertEqual(data["high"], -inf)
        self.assertEqual(data["low"], inf)
        self.assertEqual(data["close"], 0)
        self.assertEqual(data["volume"], 0)


if __name__ == "__main__":
    unittest.main()
