from .config import PORTFOLIOS, DEFAULT_N, ASSET_CODES, SMART_M, SMART_N, SMART_K, CORR_THRESHOLD, STOP_LOSS_M, STOP_LOSS_N, STOP_LOSS_K, STOP_LOSS_CORR_THRESHOLD, STOP_LOSS_PCT
from .data_loader import update_all_data
from .backtest import BacktestEngine
from .strategy import MomentumStrategy, SmartRotationStrategy, StopLossRotationStrategy
import pandas as pd

def get_trading_signal(strategy_type='momentum', **kwargs):
    """
    Generate trading signal for the next trading day.

    Args:
        strategy_type (str): 'momentum', 'smart_rotation', or 'stop_loss_rotation'
        **kwargs: Strategy parameters
            - For momentum: n (default: DEFAULT_N)
            - For smart_rotation: m, n, k, corr_threshold (default: config values)
            - For stop_loss_rotation: m, n, k, corr_threshold, stop_loss_pct (default: config values)
            - Common: update (bool, default: True)
    """
    update = kwargs.get('update', True)

    if update:
        user_input = input("是否更新数据? (y/n, 默认 n): ").strip().lower()
        if user_input == 'y':
            print("Updating data...")
            update_all_data()
        else:
            print("Skipping data update.")

    engine = BacktestEngine(start_date="20240101") # Use a reasonable lookback

    if strategy_type == 'momentum':
        n = kwargs.get('n', DEFAULT_N)
        strategy = MomentumStrategy(portfolios=PORTFOLIOS, n=n)
    elif strategy_type == 'smart_rotation':
        m = kwargs.get('m', SMART_M)
        n = kwargs.get('n', SMART_N)
        k = kwargs.get('k', SMART_K)
        corr_threshold = kwargs.get('corr_threshold', CORR_THRESHOLD)
        strategy = SmartRotationStrategy(m=m, n=n, k=k, corr_threshold=corr_threshold)
    elif strategy_type == 'stop_loss_rotation':
        m = kwargs.get('m', STOP_LOSS_M)
        n = kwargs.get('n', STOP_LOSS_N)
        k = kwargs.get('k', STOP_LOSS_K)
        corr_threshold = kwargs.get('corr_threshold', STOP_LOSS_CORR_THRESHOLD)
        stop_loss_pct = kwargs.get('stop_loss_pct', STOP_LOSS_PCT)
        strategy = StopLossRotationStrategy(m=m, n=n, k=k, corr_threshold=corr_threshold, stop_loss_pct=stop_loss_pct)
    else:
        print(f"Unknown strategy type: {strategy_type}")
        return

    # Initialize strategy data (calculates signals)
    strategy.set_data(engine.data_map, engine.aligned_open.index)
    
    print("\n" + "="*50)
    print(f"TRADING SIGNAL for Next Trading Day")

    if strategy_type == 'momentum':
        _print_momentum_signal(strategy, kwargs.get('n', DEFAULT_N))
    elif strategy_type == 'smart_rotation':
        _print_smart_rotation_signal(strategy, kwargs.get('n', SMART_N), kwargs.get('k', SMART_K))
    elif strategy_type == 'stop_loss_rotation':
        _print_stop_loss_rotation_signal(
            strategy,
            kwargs.get('n', STOP_LOSS_N),
            kwargs.get('k', STOP_LOSS_K),
            kwargs.get('stop_loss_pct', STOP_LOSS_PCT)
        )

    print("="*50)

def _print_momentum_signal(strategy, n):
    if strategy.past_n_returns is None or strategy.past_n_returns.empty:
        print("Not enough data to calculate signal.")
        return

    last_returns = strategy.past_n_returns.iloc[-1]
    last_date = strategy.past_n_returns.index[-1]
    
    if last_returns.isna().all():
         print(f"Not enough data history (Last date: {last_date}).")
         return
    
    sorted_rets = last_returns.sort_values(ascending=False)
    best_portfolio = sorted_rets.index[0]
    
    print(f"Data Date: {last_date.strftime('%Y-%m-%d')}")
    print(f"Lookback Window (N): {n} days")
    print("-" * 50)
    
    print(f"\nPortfolio Returns (Past {n} days):")
    for p, r in sorted_rets.items():
        p_name = PORTFOLIOS[p]['name']
        print(f"  {p_name:<20}: {r:>7.2%}")
        
    print("-" * 50)
    print(f"RECOMMENDATION: {PORTFOLIOS[best_portfolio]['name']}")
    
    print("\nTarget Allocation:")
    assets = PORTFOLIOS[best_portfolio]['assets']
    for asset, weight in assets.items():
        code = ASSET_CODES.get(asset, "N/A")
        print(f"  {asset:<10} ({code:<6}): {weight:.0%}")

def _print_smart_rotation_signal(strategy, n, k):
    # strategy.signals is a dict: Date -> [selected_assets]
    # strategy.factors is a DataFrame: Date x Asset -> Factor Value
    
    if not strategy.signals:
        print("Not enough data to calculate signal.")
        return
        
    # Get the last date in signals
    # Note: signals keys are dates where we have a signal
    sorted_dates = sorted(strategy.signals.keys())
    last_date = sorted_dates[-1]
    selected_assets = strategy.signals[last_date]
    
    print(f"Data Date: {last_date.strftime('%Y-%m-%d')}")
    print(f"Lookback Window (N): {n} days")
    print(f"Correlation Window (K): {k} days")
    print("-" * 50)
    
    if not selected_assets:
        print("RECOMMENDATION: Cash (No assets selected)")
        return
        
    print(f"RECOMMENDATION: Buy/Hold Selected Assets")
    print("\nTarget Allocation (Equal Weight):")
    
    weight = 1.0 / len(selected_assets)
    
    # Also show factor values for context
    if last_date in strategy.factors.index:
        factors = strategy.factors.loc[last_date]
        print(f"\nSelected Assets Details (Factor = Return/Vol):")
        for asset in selected_assets:
            code = ASSET_CODES.get(asset, "N/A")
            factor_val = factors.get(asset, float('nan'))
            print(f"  {asset:<10} ({code:<6}): {weight:.0%} (Factor: {factor_val:.4f})")
            
    else:
        for asset in selected_assets:
            code = ASSET_CODES.get(asset, "N/A")
            print(f"  {asset:<10} ({code:<6}): {weight:.0%}")

def _print_stop_loss_rotation_signal(strategy, n, k, stop_loss_pct):
    """Print trading signal for stop-loss rotation strategy."""
    if not strategy.signals:
        print("Not enough data to calculate signal.")
        return

    # Get the last date in signals
    sorted_dates = sorted(strategy.signals.keys())
    last_date = sorted_dates[-1]
    selected_assets = strategy.signals[last_date]

    print(f"Data Date: {last_date.strftime('%Y-%m-%d')}")
    print(f"Lookback Window (N): {n} days")
    print(f"Correlation Window (K): {k} days")
    print(f"Stop Loss Threshold: {stop_loss_pct:.0%}")
    print("-" * 50)

    # Show stopped assets if any
    if last_date in strategy.stopped_assets_log and strategy.stopped_assets_log[last_date]:
        stopped = strategy.stopped_assets_log[last_date]
        print(f"\n⚠ Stopped Assets (Triggered Stop Loss):")
        for asset in stopped:
            code = ASSET_CODES.get(asset, "N/A")
            print(f"  {asset:<10} ({code:<6})")
        print("-" * 50)

    if not selected_assets:
        print("RECOMMENDATION: Cash (No assets selected)")
        return

    print(f"RECOMMENDATION: Buy/Hold Selected Assets")
    print("\nTarget Allocation (Equal Weight):")

    weight = 1.0 / len(selected_assets)

    # Also show factor values for context
    if last_date in strategy.factors.index:
        factors = strategy.factors.loc[last_date]
        print(f"\nSelected Assets Details (Factor = Return/Vol):")
        for asset in selected_assets:
            code = ASSET_CODES.get(asset, "N/A")
            factor_val = factors.get(asset, float('nan'))
            print(f"  {asset:<10} ({code:<6}): {weight:.0%} (Factor: {factor_val:.4f})")
    else:
        for asset in selected_assets:
            code = ASSET_CODES.get(asset, "N/A")
            print(f"  {asset:<10} ({code:<6}): {weight:.0%}")

if __name__ == "__main__":
    get_trading_signal(strategy_type='momentum')
