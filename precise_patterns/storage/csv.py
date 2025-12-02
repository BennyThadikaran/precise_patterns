from pathlib import Path
from ..dtypes import Candle


class CSVStorage:
    def __init__(self, folder: Path | str) -> None:
        if isinstance(folder, str):
            folder = Path(folder)

        self.folder = folder.expanduser().resolve()

        if not self.folder.exists():
            self.folder.mkdir(parents=True)

        self.data = {}

    def on_candle(self, c: Candle):
        tf = c["timeframe"]
        sym = c["symbol"]

        if tf not in self.data:
            self.data[tf] = {}

        if sym not in self.data[tf]:
            self.data[tf][sym] = ["Date,Open,High,Low,Close,Volume"]

        ts = c["timestamp"].strftime("%Y-%m-%d") if tf == "D" else c["timestamp"]

        self.data[tf][sym].append(
            f"{ts},{c['open']},{c['high']},{c['low']},{c['close']},{c['volume']}"
        )

    def save(self):
        if not self.data:
            return

        for tf in self.data:
            tf_folder = self.folder / str(tf)

            if not tf_folder.exists():
                tf_folder.mkdir(parents=True)

            for sym in self.data[tf]:
                file = tf_folder / f"{sym}.csv"

                file.write_text("\n".join(self.data[tf][sym]))
