### Phase 1: Alpha Release (Current state)

Focus areas:

Deliver a working implementation capable of detecting VCP, double tops, and double bottoms.

Include full documentation and a **PyPI-ready package distribution**.

Ensure all core features are unit tested.

---

#### 🚧 Core Tasks

- [x] Implement Candle aggregation modules for EOD and minute based timeframes.
- [x] Implement Pivot detection modules
- [x] Setup pyproject and prepare for packaging & publishing

- [ ] **State management**
  - Maintain internal state to detect and correctly handle duplicate candle or pivot events
  - Prevent redundant processing or repeated event emissions

- [ ] **Tick aggregation**
  - Implement a `TickAggregator` that converts real-time websocket tick data into 1-minute OHLC candles

- [ ] **Data storage**
  - Develop a storage layer for:
    - Multi-timeframe OHLC
    - Pivot points
    - Detected patterns
  - Support both incremental and bulk inserts
  - Default backend: SQLite or DuckDB
  - Designed to be extensible to other storage engines

- [ ] **Pattern detection**
  - Implement first-phase detection modules:
    - Volatility Contraction Pattern (VCP)
    - Double Tops
    - Double Bottoms

### Phase 2: Beta Release

This phase begins once Phase 1 (Alpha) is complete.

Focus areas:

- Expand the set of supported chart patterns beyond the initial prototypes.
- Improve reliability, resolve edge cases, and address remaining bugs.
- Validate performance and stability under real-time data flow.
- Finalize documentation, usage guides, and prepare workflow for online docs.
- Prepare packaging workflow for the first public release to pypi.
