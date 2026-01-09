from .base.pattern import BasePattern, Registry
from .dtypes import Candle, Pivot, EODTimeframes
from doubly_linked_list import DoublyLinkedList
from typing import Dict


class PatternManager:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

        self.buffer: Dict[str, Dict[EODTimeframes | int, Dict[str, BasePattern]]] = {}
        self.ptn_dct = Registry.all()
        self.args = args
        self.kwargs = kwargs

    def on_pivot(self, pivot: Pivot, candle: Candle):
        symbol = pivot["symbol"]
        tf = pivot["timeframe"]

        if symbol not in self.buffer:
            self.buffer[symbol] = {}

        if tf not in self.buffer[symbol]:
            self.buffer[symbol][tf] = {}

        for name in self.ptn_dct:
            if name not in self.buffer[symbol][tf]:
                self.buffer[symbol][tf][name] = self.ptn_dct[name](
                    *self.args, **self.kwargs
                )

            self.buffer[symbol][tf][name].on_pivot(pivot, candle)


class VCP(BasePattern):
    def __init__(self) -> None:
        super().__init__()
        self.dll = DoublyLinkedList()

    def on_pivot(self, pivot: Pivot, candle: Candle):
        pass
