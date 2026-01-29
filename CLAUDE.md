# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal quantitative investment system for A-shares, implementing momentum-based rotation strategies for ETF/LOF trading. Data is sourced from `akshare`.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive menu system (main entry point)
python main.py

# Update market data (incremental by default)
python -m src.data_loader

# Run backtest
python -m src.backtest

# Get next-day trading signal
python -m src.trading_signal                                    # Momentum strategy (default)
python -m src.trading_signal --strategy smart_rotation --m 3    # Smart rotation strategy

# Parameter optimization
python -m src.optimize
```

## Architecture

### Core Components

- **`src/strategy.py`**: Abstract `Strategy` base class with two implementations:
  - `MomentumStrategy`: Selects best-performing portfolio from 4 predefined scenarios (bull surge, slow bull, slow bear, panic) based on N-day momentum
  - `SmartRotationStrategy`: Selects M assets from entire pool using risk-adjusted momentum (return/volatility) with correlation filtering

- **`src/backtest.py`**: `BacktestEngine` - Event-driven backtester with T+1 execution (signal on T close, execute at T+1 open). Handles portfolio rebalancing and commission costs.

- **`src/data_loader.py`**: Fetches and caches ETF daily data via akshare. Supports incremental and full updates. Data stored in `data/` directory as CSV files.

- **`src/config.py`**: Asset code mappings (`ASSET_CODES`), portfolio definitions (`PORTFOLIOS`), and strategy parameters.

- **`src/trading_signal.py`**: Generates live trading recommendations.

- **`src/optimize.py`**: Grid search optimization for strategy parameters using Calmar ratio.

### Data Flow

1. `data_loader.py` fetches OHLCV data from akshare → saves to `data/{code}.csv`
2. `BacktestEngine._prepare_data()` loads and aligns data across assets (forward-fill for different trading calendars)
3. Strategy's `on_data_loaded()` pre-computes signals for all dates
4. `get_target_weights(date)` returns position weights using previous day's signal (T-1 signal → T open execution)

### Strategy Signal Logic

Both strategies use **T-1 signal for T execution**: the signal generated at day T-1's close determines positions entered at day T's open. This simulates realistic trading where you can only act on yesterday's closing data.

## Key Configuration (src/config.py)

- `DEFAULT_N = 20`: Momentum lookback window (optimized)
- `SMART_M = 3`: Number of assets to hold in smart rotation
- `SMART_N = 30`: Factor calculation window
- `SMART_K = 100`: Correlation calculation window
- `CORR_THRESHOLD = 0.9`: Max correlation between selected assets
- `COMMISSION_RATE = 0.0003`: Round-trip commission
