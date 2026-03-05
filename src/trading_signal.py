from .config import (
    SECTOR_ASSET_CODES,
    SECTOR_M, SECTOR_N, SECTOR_K, SECTOR_CORR_THRESHOLD, SECTOR_STOP_LOSS_PCT,
    SORTINO_M, SORTINO_N, SORTINO_K, SORTINO_CORR_THRESHOLD, SORTINO_STOP_LOSS_PCT,
)
from .data_loader import update_all_data, load_all_data
from .backtest import BacktestEngine
from .strategy import SectorRotationStrategy, SortinoRotationStrategy

# Strategy registry for extensibility
STRATEGY_REGISTRY = {
    'sector_rotation': {
        'class': SectorRotationStrategy,
        'asset_codes': SECTOR_ASSET_CODES,
        'default_params': {
            'm': SECTOR_M, 'n': SECTOR_N, 'k': SECTOR_K,
            'corr_threshold': SECTOR_CORR_THRESHOLD,
            'stop_loss_pct': SECTOR_STOP_LOSS_PCT
        }
    },
    'sortino_rotation': {
        'class': SortinoRotationStrategy,
        'asset_codes': SECTOR_ASSET_CODES,
        'default_params': {
            'm': SORTINO_M, 'n': SORTINO_N, 'k': SORTINO_K,
            'corr_threshold': SORTINO_CORR_THRESHOLD,
            'stop_loss_pct': SORTINO_STOP_LOSS_PCT
        }
    },
}


def get_trading_signal(strategy_type='sector_rotation', **kwargs):
    """
    Generate trading signal for the next trading day.

    Args:
        strategy_type (str): 'sector_rotation'
        **kwargs: Strategy parameters (m, n, k, corr_threshold, stop_loss_pct, update)
    """
    if strategy_type not in STRATEGY_REGISTRY:
        print(f"Unknown strategy type: {strategy_type}")
        return

    config = STRATEGY_REGISTRY[strategy_type]
    asset_codes = config['asset_codes']
    defaults = config['default_params']

    # Data update
    update = kwargs.get('update', True)
    if update:
        user_input = input("是否更新数据? (y/n, 默认 n): ").strip().lower()
        if user_input == 'y':
            print("Updating data...")
            update_all_data(assets_to_update=list(asset_codes.items()))
        else:
            print("Skipping data update.")

    # Load data
    data_map = load_all_data(asset_codes=asset_codes)
    engine = BacktestEngine(start_date="20240101", data_map=data_map)

    # Create strategy with merged parameters
    params = {k: kwargs.get(k, v) for k, v in defaults.items()}
    strategy = config['class'](**params)
    strategy.set_data(engine.data_map, engine.aligned_open.index)

    # Print signal
    print("\n" + "="*50)
    print("TRADING SIGNAL for Next Trading Day")
    _print_signal(strategy, params['n'], params['k'], params['stop_loss_pct'])
    print("="*50)


def _print_signal(strategy, n, k, stop_loss_pct):
    """Print trading signal for rotation strategy."""
    if not strategy.signals:
        print("Not enough data to calculate signal.")
        return

    asset_codes = strategy.asset_codes
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
            code = asset_codes.get(asset, "N/A")
            print(f"  {asset:<10} ({code:<6})")
        print("-" * 50)

    if not selected_assets:
        print("RECOMMENDATION: Cash (No assets selected)")
        return

    print("RECOMMENDATION: Buy/Hold Selected Assets")

    weight = 1.0 / len(selected_assets)
    print("\nTarget Allocation (Equal Weight):")

    if last_date in strategy.factors.index:
        factors = strategy.factors.loc[last_date]
        factor_label = "Return/DownsideVol" if isinstance(strategy, SortinoRotationStrategy) else "Return/Vol"
        print(f"\nSelected Assets Details (Factor = {factor_label}):")
        for asset in selected_assets:
            code = asset_codes.get(asset, "N/A")
            factor_val = factors.get(asset, float('nan'))
            print(f"  {asset:<10} ({code:<6}): {weight:.0%} (Factor: {factor_val:.4f})")
    else:
        for asset in selected_assets:
            code = asset_codes.get(asset, "N/A")
            print(f"  {asset:<10} ({code:<6}): {weight:.0%}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate trading signal')
    parser.add_argument('--strategy', type=str, default='sector_rotation',
                        choices=list(STRATEGY_REGISTRY.keys()),
                        help='Strategy type')
    args = parser.parse_args()
    get_trading_signal(strategy_type=args.strategy)
