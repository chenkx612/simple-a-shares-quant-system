from .config import (
    ASSET_CODES,
    STOP_LOSS_M, STOP_LOSS_N, STOP_LOSS_K, STOP_LOSS_CORR_THRESHOLD, STOP_LOSS_PCT,
    SECTOR_ASSET_CODES, SECTOR_M, SECTOR_N, SECTOR_K, SECTOR_CORR_THRESHOLD, SECTOR_STOP_LOSS_PCT
)
from .data_loader import update_all_data, load_all_data
from .backtest import BacktestEngine
from .strategy import StopLossRotationStrategy, SectorRotationStrategy
import pandas as pd

def get_trading_signal(strategy_type='stop_loss_rotation', **kwargs):
    """
    Generate trading signal for the next trading day.

    Args:
        strategy_type (str): 'stop_loss_rotation' or 'sector_rotation'
        **kwargs: Strategy parameters
            - For stop_loss_rotation: m, n, k, corr_threshold, stop_loss_pct (default: config values)
            - For sector_rotation: m, n, k, corr_threshold, stop_loss_pct (default: SECTOR_* values)
            - Common: update (bool, default: True)
    """
    update = kwargs.get('update', True)

    # 确定要更新的资产池
    if strategy_type == 'sector_rotation':
        assets_to_update = list(SECTOR_ASSET_CODES.items())
    else:
        assets_to_update = list(ASSET_CODES.items())

    if update:
        user_input = input("是否更新数据? (y/n, 默认 n): ").strip().lower()
        if user_input == 'y':
            print("Updating data...")
            update_all_data(assets_to_update=assets_to_update)
        else:
            print("Skipping data update.")

    # 根据策略类型加载对应的资产池数据
    if strategy_type == 'sector_rotation':
        data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
    else:
        data_map = load_all_data(asset_codes=ASSET_CODES)

    engine = BacktestEngine(start_date="20240101", data_map=data_map)

    if strategy_type == 'stop_loss_rotation':
        m = kwargs.get('m', STOP_LOSS_M)
        n = kwargs.get('n', STOP_LOSS_N)
        k = kwargs.get('k', STOP_LOSS_K)
        corr_threshold = kwargs.get('corr_threshold', STOP_LOSS_CORR_THRESHOLD)
        stop_loss_pct = kwargs.get('stop_loss_pct', STOP_LOSS_PCT)
        strategy = StopLossRotationStrategy(m=m, n=n, k=k, corr_threshold=corr_threshold, stop_loss_pct=stop_loss_pct)
    elif strategy_type == 'sector_rotation':
        m = kwargs.get('m', SECTOR_M)
        n = kwargs.get('n', SECTOR_N)
        k = kwargs.get('k', SECTOR_K)
        corr_threshold = kwargs.get('corr_threshold', SECTOR_CORR_THRESHOLD)
        stop_loss_pct = kwargs.get('stop_loss_pct', SECTOR_STOP_LOSS_PCT)
        strategy = SectorRotationStrategy(m=m, n=n, k=k, corr_threshold=corr_threshold, stop_loss_pct=stop_loss_pct)
    else:
        print(f"Unknown strategy type: {strategy_type}")
        return

    # Initialize strategy data (calculates signals)
    strategy.set_data(engine.data_map, engine.aligned_open.index)

    print("\n" + "="*50)
    print(f"TRADING SIGNAL for Next Trading Day")

    if strategy_type == 'stop_loss_rotation':
        _print_stop_loss_rotation_signal(
            strategy,
            kwargs.get('n', STOP_LOSS_N),
            kwargs.get('k', STOP_LOSS_K),
            kwargs.get('stop_loss_pct', STOP_LOSS_PCT)
        )
    elif strategy_type == 'sector_rotation':
        _print_sector_rotation_signal(
            strategy,
            kwargs.get('n', SECTOR_N),
            kwargs.get('k', SECTOR_K),
            kwargs.get('stop_loss_pct', SECTOR_STOP_LOSS_PCT)
        )

    print("="*50)

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


def _print_sector_rotation_signal(strategy, n, k, stop_loss_pct):
    """Print trading signal for sector rotation strategy."""
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
            code = SECTOR_ASSET_CODES.get(asset, "N/A")
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
            code = SECTOR_ASSET_CODES.get(asset, "N/A")
            factor_val = factors.get(asset, float('nan'))
            print(f"  {asset:<10} ({code:<6}): {weight:.0%} (Factor: {factor_val:.4f})")
    else:
        for asset in selected_assets:
            code = SECTOR_ASSET_CODES.get(asset, "N/A")
            print(f"  {asset:<10} ({code:<6}): {weight:.0%}")


if __name__ == "__main__":
    get_trading_signal(strategy_type='stop_loss_rotation')
