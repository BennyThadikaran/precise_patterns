Readers
-------

This module provides efficient and flexible helper classes for reading CSV files with OHLC time-series data.

It includes the :class:`~precise_patterns.readers.csv.CSVReader` class, which:

* Streams data lazily to minimize memory usage
* Supports direct reading from filesystem folders
* Handles customizable CSV column headers
* Allows optional fast-seeking from a given start date
* Parses timestamps automatically or with a user-supplied format
* Produces structured :class:`OHLC` typed dictionaries

This module assumes that CSV files contain chronological data sorted in
ascending, monotonic order (earliest → latest), which enables efficient
backward-seeking when applying a ``from_date`` filter.

It is particularly useful when working with large historical datasets.

.. automodule:: precise_patterns.readers.csv
   :members:
   :private-members:
   :show-inheritance:
