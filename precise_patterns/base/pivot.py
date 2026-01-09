from abc import ABC, abstractmethod
from ..dtypes import Candle
from typing import Dict


class BasePivotDetector(ABC):
    """
    A Base class for PivotDetector classes
    """

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def on_candle_close(self, candle: Candle) -> None:
        """
        Handle a newly closed candle. Must be implemented

        :param Candle candle: The completed candle to process.
        """
        pass

    def pack(self) -> dict:
        """
        Serialize the object's internal state into a dictionary.

        This method returns a shallow dictionary representation of the
        instance's attributes, suitable for storage, logging, or transferring
        state between processes.

        :returns dict: A dictionary containing the object's internal attributes.
        """
        return self.__dict__

    def unpack(self, data: Dict) -> None:
        """
        Restore the object's internal state from a dictionary.

        This method updates the instance's attributes using the provided
        dictionary. Any keys in ``data`` matching existing attributes will
        overwrite them.
        """
        self.__dict__.update(data)
