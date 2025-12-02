# Precise Patterns

**Precise Patterns** is a Python library for real-time detection of stock market chart patterns.
It provides flexible candle aggregation, pivot detection, and pattern recognition tools designed
for live trading systems and historical backtesting workflows.

Supports: **Python 3.10 or higher**

---

## ✨ Features

`precise_patterns` is the next major iteration of my earlier project, **Stock-Patterns**.

- **Multi-timeframe candle aggregation**
  - Intraday (minute-based) and end-of-day aggregation.
  - Supports arbitrary custom minute frequencies (e.g., 3, 5, 15, 75, 240…)
  - Accurate handling of sessions, weekends, and holidays
  - Uses event-driven architecture for streaming updates

- **Pivot point identification**
  - Detect local highs and lows with configurable rules
  - Automatically triggered from candle close events

- **Pattern detection engine**
  - A fresh, reimagined approach to pattern detection algorithms (in progress)
  - Pluggable architecture for future expansion

- **Typed data models**
  - `Candle`, `OHLC`, and `Pivot`
  - Built using `TypedDict` for structural validation and IDE code completion for fields.

---

## 🔌 Event-Driven Architecture

`precise_patterns` is built around a central event bus:

- Aggregators emit `"candle.close"` events with a `Candle` payload
- Pivot and pattern modules subscribe and react to those events
- Enables real-time streaming and modular processing pipelines

Users may register their own handlers to stream or store detected structures.

---

```kotlin
     ╭──────────────╮
     │  DataReader  │
     │   csv, db,   │
     │  websocket   │
     ╰──────┬───────╯
          Candle
            ▼
     ╭──────────────╮
     │  Aggregator  │
     ╰──────┬───────╯
      candle.closed
    ╭───────┴─────────╮
    ▼                 ▼
╭─────────────╮  ╭──────────╮
│PivotDetector│  │  Storage │
╰─────┬───────╯  ╰────┬─────╯
      │               ▲
  pivot.formed   pattern.formed
      ▼               │
╭───────────────╮     │   Output
│PatternDetector│──────► patterns
╰───────────────╯        to Chart
```

## 🔧 Components Overview

| Component          | Purpose                                                   |
| ------------------ | --------------------------------------------------------- |
| `CandleBuilder`    | Accumulates OHLC updates within a timeframe               |
| `MinuteAggregator` | Groups tick or 1m candles into higher intraday timeframes |
| `EODAggregator`    | Resamples daily candles into D/W/M/Q intervals            |
| `PivotDetector`    | Emits local pivot highs/lows as they form                 |

All components are designed to be composable and stateful.

**Notes**

- The CSVReader is an experimental custom CSV reader. It is not fully tested.
- The CSVStorage class is temporary class written for debug (not feature complete)
- Both of the above classes may not exist in the final implementation.

## Example

See `example.py` for a partial implementation.

## Documentation

To generate the docs using sphinx:

1. Install dependencies: `pip install sphinx furo`

2. Build the docs: `sphinx-build docs/source docs/build`

3. Open `docs/build/index.html` in your browser.

---

## 📦 Installation

The package has not been published yet.

For those wishing to tinker, clone or download the repo and run `pip install <path to repo>`

To install doc dependencies, `pip install <path to repo>[docs]`

## Task and Future roadmap

See [tasks.md](tasks.md)
