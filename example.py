from datetime import time
from pathlib import Path
from precise_patterns.aggregator import MinuteAggregator
from precise_patterns.dtypes import Candle, Pivot
from precise_patterns.events import event_bus
from precise_patterns.pivots import PivotDetector
from precise_patterns.readers.csv import CSVReader
from precise_patterns.storage.csv import CSVStorage


def on_pivot_confirm(pivot: Pivot, candle: Candle):
    """
    Handler that prints pivots to screen.

    In actual use, this would be a pattern detection class
    """
    print("Pivot:", pivot)


DIR = Path(__file__).parent

agg = MinuteAggregator(
    filter_timeframes=[5, 15, 30, 60, 75, 120, 240],
    start_time=time(9, 15),
    end_time=time(15, 30),
)

reader = CSVReader(
    data_folder="~/Desktop/",
    date_format="%Y-%m-%dT%H:%M:%S%z",
)

# specify folder path to store CSV files
storage = CSVStorage(folder=DIR / "candles")

pivots = PivotDetector()

# Attach event handlers
event_bus.add_listener("candle.close", pivots.on_candle_close)
event_bus.add_listener("candle.close", storage.on_candle)
event_bus.add_listener("pivot.confirm", on_pivot_confirm)

for row in reader.stream("ashokley"):
    agg.on_candle_close("ashokley", *row.values())

storage.save()
