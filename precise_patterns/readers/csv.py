from ..dtypes import OHLC
from typing import Generator, Optional, BinaryIO
from datetime import datetime
from dateutil.parser import parse
from pathlib import Path
import os


class CSVReader:
    """
    Read OHLC CSV data from a directory and stream parsed rows lazily.

    This class supports partial reading from a specific starting date and
    customizable CSV column mappings.

    :param data_folder: Path to a directory containing CSV files.
    :type data_folder: :class:`pathlib.Path` | :class:`str`
    :param column_map: Optional mapping from CSV column names to internal field names.
        If None, column headers would be assumed as Date, Open, High, Low, Close, Volume.

        **Example**
        For CSV with columns headers like `Datetime`, `O`, `H`, `L`, `C`, `V`

        .. code-block:: python

            # Map provider-specific column names to standard ones
            column_map = {
                "DateTime": "date",
                "O": "open",
                "H": "high",
                "L": "low",
                "C": "close",
                "V": "volume",
            }

            reader = CSVReader("~/.data", column_map=column_map)
    :type column_map: :class:`dict` | None
    :param date_format: Explicit format string for timestamps. If not provided,
        automatic parsing via :func:`dateutil.parser.parse` is used.
    :type date_format: :class:`str` | None
    :param from_date: When set, rows older than this timestamp are skipped efficiently.
    :type from_date: :class:`datetime.datetime` | None

    .. note::
       Providing a ``date_format`` is **strongly recommended** when performance
       and high-volume streaming are important, since auto-detection of formats
       incurs noticeable overhead.

    .. note::
        The implementation relies on timestamps being sorted in ascending,
        monotonic order (earliest → latest).

    .. seealso::
       :class:`OHLC`
    """

    def __init__(
        self,
        data_folder: Path | str,
        column_map: Optional[dict] = None,
        date_format: Optional[str] = None,
        from_date: Optional[datetime] = None,
    ) -> None:
        if isinstance(data_folder, str):
            data_folder = Path(data_folder)

        self.data_folder = data_folder.expanduser().resolve()

        self.date_format = date_format
        self.from_date = from_date

        self.col_map = dict(
            Date="date",
            Open="open",
            High="high",
            Low="low",
            Close="close",
            Volume="volume",
        )

        if column_map:
            self.col_map.update(column_map)

    def parse_datetime(self, dt_str: str):
        """
        Parse a datetime string into a :class:`datetime.datetime` object.

        If a custom ``date_format`` was provided during initialization,
        :func:`datetime.datetime.strptime` is used to parse the timestamp.
        Otherwise, :func:`dateutil.parser.parse` performs automatic detection.

        :param dt_str: The timestamp string extracted from a CSV row.
        :type dt_str: :class:`str`
        :return: Parsed datetime with timezone removed if present.
        :rtype: :class:`datetime.datetime`
        :raises ValueError: If parsing fails for both custom format and auto parsing.

        .. seealso:: :meth:`stream`
        """

        if self.date_format:
            dt = datetime.strptime(dt_str, self.date_format)
        else:
            dt = parse(dt_str)

        return dt.replace(tzinfo=None) if dt.tzinfo else dt

    def to_dict(self, values) -> OHLC:
        """
        Convert a list of CSV values into an OHLC dictionary structure.

        This method uses column index mappings inferred from CSV headers during
        streaming and applies type conversion.

        :param values: Parsed CSV row split into fields.
        :type values: :class:`list`\\[:class:`str`]
        :return: Parsed values mapped to the :class:`OHLC` schema.
        :rtype: :class:`OHLC`

        .. note::
           This helper method assumes ``self._col_idx_map`` has been initialized
           via :meth:`stream`.
        """
        return OHLC(
            timestamp=self.parse_datetime(values[self._col_idx_map["date"]]),
            open=float(values[self._col_idx_map["open"]]),
            high=float(values[self._col_idx_map["high"]]),
            low=float(values[self._col_idx_map["low"]]),
            close=float(values[self._col_idx_map["close"]]),
            volume=float(values[self._col_idx_map["volume"]]),
        )

    def read_line(self, f: BinaryIO, offset: int = -2) -> bytes:
        """
        Read a line from the file by seeking backward from the file end.

        This method is optimized for quickly locating the last line(s) in a large CSV.

        :param f: Open binary file object.
        :type f: :class:`typing.BinaryIO`
        :param offset: Negative byte offset relative to end of file.
        :type offset: :class:`int`
        :return: The located line, including the newline suffix.
        :rtype: :class:`bytes`
        :raises OSError: If the file is too short to seek backward.

        .. warning::
           This method updates ``self.pos`` to mark current file seek position.
        """
        try:
            # seek 2 bytes to the last line ending ( \n )
            f.seek(offset, os.SEEK_END)

            # seek backwards 2 bytes till the next line ending
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)

        except OSError:
            # catch OSError in case of a one line file
            f.seek(0)

        self.pos = f.tell()
        # we have the last line
        return f.readline()

    def stream(self, name: str) -> Generator[OHLC, None, None]:
        """
        Lazily read and yield OHLC rows from a CSV file.

        The file is expected to live in ``data_folder`` and be named
        ``<name>.csv``. Yields rows in forward chronological order.
        If ``from_date`` was set, binary search–like seeking is used
        to start near the required date efficiently.

        :param name: Base filename without the ``.csv`` extension.
        :type name: :class:`str`
        :yield: Parsed OHLC rows.
        :rtype: :class:`typing.Generator`\\[:class:`OHLC`, None, None]
        :raises FileNotFoundError: If the CSV does not exist.
        :raises ValueError: If datetime in CSV cannot be parsed.

        **Example**

        .. code-block:: python

            reader = CSVReader("~/data", from_date=datetime(2024, 1, 1))
            for row in reader.stream("BTCUSD"):
                print(row["timestamp"], row["close"])

        .. seealso::
           :meth:`parse_datetime`
           :meth:`to_dict`
        """
        line_found = False

        self.file = self.data_folder / f"{name}.csv"

        size = os.path.getsize(self.file)

        with self.file.open("rb") as f:
            columns = f.readline().strip().decode("utf-8").split(",")
            size = size - f.tell()

            # Map column names to positional index
            self._col_idx_map = {
                self.col_map[k]: i for i, k in enumerate(columns) if k in self.col_map
            }

            if not self.from_date:
                while line := f.readline():
                    yield self.to_dict(line.strip().decode("utf-8").split(","))
                return

            line = self.read_line(f)

            dt = self.parse_datetime(line[0 : line.find(b",")].decode("utf-8"))

            days_diff = (dt - self.from_date).days
            line_length = len(line)

            line = self.read_line(f, max(-size, -days_diff * line_length))

            dt = self.parse_datetime(line[0 : line.find(b",")].decode("utf-8"))

            line_found = dt == self.from_date

            if not line_found and dt > self.from_date:
                while not line_found:
                    line = self.read_line(f, -self.pos - line_length)
                    dt = self.parse_datetime(line[0 : line.find(b",")].decode("utf-8"))

                    if dt >= self.from_date:
                        line_found = True
                        break

            while line := f.readline():
                if not line_found:
                    dt = self.parse_datetime(line[0 : line.find(b",")].decode("utf-8"))

                    if dt >= self.from_date:
                        line_found = True
                        yield self.to_dict(line.strip().decode("utf-8").split(","))
                else:
                    yield self.to_dict(line.strip().decode("utf-8").split(","))
