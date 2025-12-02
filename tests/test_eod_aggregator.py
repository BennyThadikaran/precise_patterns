from math import inf
import unittest
import unittest.mock
import context
import helpers
from datetime import date, datetime
from precise_patterns.candles.aggregator import EODAggregator

event_bus_module_path = "precise_patterns.candles.aggregator.event_bus"


def make_dt(d: str):
    return datetime.strptime(d, "%Y-%m-%d")


class TestEODAggregator(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_bus = helpers.FakeBus()
        self.agg = EODAggregator(filter_timeframes=["D"])

    def test_get_monthend(self):
        """
        Tests for EODAggregator.get_monthend

        1. No holidays or weekends
        2. Market ending on Fri and monthend on Sat
        3. Month ending is a market holiday
        4. Market ending on Fri, month ending with holidays and weekends

        """
        # No holidays or weekends
        agg = EODAggregator(filter_timeframes=["D"])

        self.assertEqual(
            agg.get_monthend(date(2025, 1, 1)),
            date(2025, 1, 31),
        )

        # Market ending on Fri and monthend on Sat
        agg.last_weekday = 4

        self.assertEqual(
            agg.get_monthend(date(2025, 5, 1)),
            date(2025, 5, 30),
        )

        # Month ending is a market holiday
        agg.holidays = {date(2025, 1, 31)}

        self.assertEqual(
            agg.get_monthend(date(2025, 1, 1)),
            date(2025, 1, 30),
        )

        # Market ending on Fri, month ending with holidays and weekends
        agg.last_weekday = 4
        agg.holidays = {date(2025, 3, 31)}

        self.assertEqual(
            agg.get_monthend(date(2025, 3, 1)),
            date(2025, 3, 28),
        )

        # Market ending on Fri, month ending with extra_session
        agg.last_weekday = 4
        agg.extra_sessions = {date(2025, 5, 31)}

        self.assertEqual(
            agg.get_monthend(date(2025, 5, 1)),
            date(2025, 5, 31),
        )

    def test_get_weekend(self):
        # default returns Saturday
        agg = EODAggregator(filter_timeframes=["D"])

        self.assertEqual(
            agg.get_weekend(date(2025, 1, 1)),
            date(2025, 1, 4),
        )

        # Market closes friday, returns friday
        agg.last_weekday = 4

        self.assertEqual(
            agg.get_weekend(date(2025, 1, 1)),
            date(2025, 1, 3),
        )

        # On Friday, Market closes friday, returns friday
        agg.last_weekday = 4

        self.assertEqual(
            agg.get_weekend(date(2025, 1, 4)),
            date(2025, 1, 4),
        )

        # On Sunday, by default returns Saturday
        agg.last_weekday = 5

        self.assertEqual(
            agg.get_weekend(date(2024, 12, 29)),
            date(2025, 1, 4),
        )

        # Market closes Friday, adjusts backward for holidays
        agg.last_weekday = 4
        agg.holidays = {date(2025, 1, 3), date(2025, 1, 2)}

        self.assertEqual(
            agg.get_weekend(date(2025, 1, 1)),
            date(2025, 1, 1),
        )

        # Market closes Friday, with extra session on Saturday
        # returns Saturday
        agg.last_weekday = 4
        agg.holidays = {date(2025, 1, 3)}
        agg.extra_sessions = {date(2025, 1, 4)}

        self.assertEqual(
            agg.get_weekend(date(2025, 1, 1)),
            date(2025, 1, 4),
        )

    def test_first_quarter_end(self):
        """January, February, and March should map to March's monthend."""
        agg = EODAggregator()
        for month in (1, 2, 3):
            result = agg.get_quarter_end(date(2024, month, 15))
            self.assertEqual(result, date(2024, 3, 31))

    def test_second_quarter_end(self):
        """April–June should end in June."""
        agg = EODAggregator()

        for month in (4, 5, 6):
            result = agg.get_quarter_end(date(2024, month, 1))
            self.assertEqual(result, date(2024, 6, 30))

    def test_third_quarter_end(self):
        """July–September should end in September."""
        agg = EODAggregator()

        for month in (7, 8, 9):
            result = agg.get_quarter_end(date(2024, month, 10))
            self.assertEqual(result, date(2024, 9, 30))

    def test_fourth_quarter_end(self):
        """October–December should end in December."""
        agg = EODAggregator()

        for month in (10, 11, 12):
            result = agg.get_quarter_end(date(2024, month, 25))
            self.assertEqual(result, date(2024, 12, 31))

    def test_year_rollover_no_issue(self):
        """Verify December doesn't incorrectly roll into next quarter/year."""
        agg = EODAggregator()
        result = agg.get_quarter_end(date(2023, 12, 31))
        self.assertEqual(result, date(2023, 12, 31))

    @unittest.mock.patch(event_bus_module_path)
    def test_daily_candle_event_emitted(self, mock_bus: unittest.mock.Mock):
        """
        Verify that a daily timeframe candle emits
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        agg = EODAggregator(filter_timeframes=["D"])

        agg.on_candle_close("AAPL", make_dt("2024-01-02"), 100, 110, 95, 105, 1000)

        self.assertEqual(len(self.fake_bus.calls), 1)

        evt = self.fake_bus.calls[0][0]
        self.assertEqual(evt["timeframe"], "D")
        self.assertEqual(evt["symbol"], "AAPL")

    @unittest.mock.patch(event_bus_module_path)
    def test_week_close_event_on_weekend(self, mock_bus):
        """
        Ensure weekly timeframe emits, when the week ends
        (Saturday default).
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        dt = make_dt("2024-01-06")  # Saturday

        agg = EODAggregator(filter_timeframes=["W"])
        agg.on_candle_close("AAPL", dt, 10, 12, 9, 11, 200)

        self.assertEqual(len(self.fake_bus.calls), 1)
        self.assertEqual(self.fake_bus.calls[0][0]["timeframe"], "W")

    @unittest.mock.patch(event_bus_module_path)
    def test_month_close_event_at_end(self, mock_bus):
        """
        Confirm a monthly candle event is emitted on the final day of the month.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        agg = EODAggregator(filter_timeframes=["M"])
        agg.on_candle_close("AAPL", make_dt("2024-01-31"), 50, 52, 49, 51, 500)

        self.assertEqual(len(self.fake_bus.calls), 1)
        self.assertEqual(self.fake_bus.calls[0][0]["timeframe"], "M")

    @unittest.mock.patch(event_bus_module_path)
    def test_quarter_close_event_at_end(self, mock_bus):
        """
        Confirm a quarterly candle event is emitted on a quarter-ending date.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        agg = EODAggregator(filter_timeframes=["Q"])
        agg.on_candle_close("AAPL", make_dt("2024-03-31"), 60, 65, 59, 62, 900)

        self.assertEqual(len(self.fake_bus.calls), 1)
        self.assertEqual(self.fake_bus.calls[0][0]["timeframe"], "Q")

    @unittest.mock.patch(event_bus_module_path)
    def test_no_events_when_timeframe_filtered_out(self, mock_bus):
        """
        Ensure events are not emitted for excluded timeframes in filter_timeframes.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        dt = make_dt("2024-01-02")  # Tues - only daily event could be emitted

        agg = EODAggregator(filter_timeframes=["W"])
        agg.on_candle_close("AAPL", dt, 100, 110, 95, 105, 1000)

        self.assertEqual(len(self.fake_bus.calls), 0)

    @unittest.mock.patch(event_bus_module_path)
    def test_multiple_events_and_reset_logic(self, mock_bus):
        """
        Test multiple emissions (daily + weekly) and verify builder state resets after each event.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        agg = EODAggregator(filter_timeframes=["D", "W"])
        agg.on_candle_close("AAPL", make_dt("2024-01-05"), 10, 15, 9, 14, 100)
        agg.on_candle_close("AAPL", make_dt("2024-01-06"), 14, 16, 13, 15, 150)

        self.assertEqual(len(self.fake_bus.calls), 3)
        self.assertEqual(self.fake_bus.calls[-1][0]["timeframe"], "W")
        self.assertEqual(self.fake_bus.calls[-2][0]["timeframe"], "D")

        data = agg.data["AAPL"]["W"].data
        self.assertEqual(data["open"], 0)
        self.assertEqual(data["high"], -inf)
        self.assertEqual(data["low"], inf)
        self.assertEqual(data["close"], 0)
        self.assertEqual(data["volume"], 0)

    @unittest.mock.patch(event_bus_module_path)
    def test_holiday_adjusted_weekend(self, mock_bus):
        """
        Test that weekend boundary shifts earlier, when a holiday falls on the expected closing day.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        agg = EODAggregator(
            filter_timeframes=["W"],
            holidays=[date(2024, 1, 5)],
            last_weekday=4,
        )
        agg.on_candle_close("AAPL", make_dt("2024-01-04"), 20, 25, 19, 23, 300)

        self.assertEqual(len(self.fake_bus.calls), 1)
        self.assertEqual(self.fake_bus.calls[0][0]["timeframe"], "W")

    @unittest.mock.patch(event_bus_module_path)
    def test_extra_session_extends_week(self, mock_bus):
        """
        Validate that extra sessions extend week close to the latest additional trading day.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        agg = EODAggregator(
            filter_timeframes=["W"],
            extra_sessions=[date(2024, 1, 6)],
            last_weekday=5,
        )

        agg.on_candle_close("AAPL", make_dt("2024-01-06"), 40, 45, 39, 41, 200)

        self.assertEqual(len(self.fake_bus.calls), 1)
        self.assertEqual(self.fake_bus.calls[0][0]["timeframe"], "W")

    @unittest.mock.patch(event_bus_module_path)
    def test_multiple_symbols_independent_aggregation(self, mock_bus):
        """
        Ensure different symbols maintain separate aggregation state and emit independent events.
        """
        mock_bus.emit.side_effect = self.fake_bus.emit

        agg = EODAggregator(filter_timeframes=["D"])
        agg.on_candle_close("AAPL", make_dt("2024-01-02"), 100, 110, 95, 105, 1000)
        agg.on_candle_close("MSFT", make_dt("2024-01-02"), 200, 210, 195, 205, 1500)

        self.assertEqual(len(self.fake_bus.calls), 2)

        symbols = {evt[0]["symbol"] for evt in self.fake_bus.calls}

        self.assertEqual(symbols, {"AAPL", "MSFT"})


if __name__ == "__main__":
    unittest.main()
