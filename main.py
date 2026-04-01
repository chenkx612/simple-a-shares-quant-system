import sys
from src.data_loader import update_all_data, load_all_data
from src.backtest import BacktestEngine
from src.optimize import optimize_sector_params, optimize_factor_threshold_params, optimize_ewma_factor_threshold_params
from src.trading_signal import get_trading_signal
from src.config import (
    SECTOR_ASSET_CODES, SECTOR_M, SECTOR_N, SECTOR_K, SECTOR_CORR_THRESHOLD, SECTOR_STOP_LOSS_PCT,
    FACTOR_THRESHOLD_M, FACTOR_THRESHOLD_N, FACTOR_THRESHOLD_K,
    FACTOR_THRESHOLD_CORR_THRESHOLD, FACTOR_THRESHOLD_STOP_LOSS_PCT, FACTOR_THRESHOLD_LOWER_BOUND,
    FACTOR_EWMA_M, FACTOR_EWMA_N, FACTOR_EWMA_K,
    FACTOR_EWMA_CORR_THRESHOLD, FACTOR_EWMA_STOP_LOSS_PCT, FACTOR_EWMA_LOWER_BOUND,
)
from src.strategy import SectorRotationStrategy, FactorThresholdRotationStrategy, EWMAFactorThresholdRotationStrategy

STRATEGIES = {
    '1': {
        'name': '行业轮动 - Sharpe因子 (Return/Vol)',
        'type': 'sector_rotation',
        'class': SectorRotationStrategy,
        'params': lambda: dict(m=SECTOR_M, n=SECTOR_N, k=SECTOR_K,
                               corr_threshold=SECTOR_CORR_THRESHOLD, stop_loss_pct=SECTOR_STOP_LOSS_PCT),
        'optimize': optimize_sector_params,
    },
    '2': {
        'name': '行业轮动 - 因子下限 (Factor Threshold)',
        'type': 'factor_threshold_rotation',
        'class': FactorThresholdRotationStrategy,
        'params': lambda: dict(m=FACTOR_THRESHOLD_M, n=FACTOR_THRESHOLD_N, k=FACTOR_THRESHOLD_K,
                               corr_threshold=FACTOR_THRESHOLD_CORR_THRESHOLD,
                               stop_loss_pct=FACTOR_THRESHOLD_STOP_LOSS_PCT,
                               factor_lower_bound=FACTOR_THRESHOLD_LOWER_BOUND),
        'optimize': optimize_factor_threshold_params,
    },
    '3': {
        'name': '行业轮动 - EWMA因子下限 (EWMA Factor Threshold)',
        'type': 'ewma_factor_threshold_rotation',
        'class': EWMAFactorThresholdRotationStrategy,
        'params': lambda: dict(m=FACTOR_EWMA_M, n=FACTOR_EWMA_N, k=FACTOR_EWMA_K,
                               corr_threshold=FACTOR_EWMA_CORR_THRESHOLD,
                               stop_loss_pct=FACTOR_EWMA_STOP_LOSS_PCT,
                               factor_lower_bound=FACTOR_EWMA_LOWER_BOUND),
        'optimize': optimize_ewma_factor_threshold_params,
    },
}


def print_asset_pnl(engine):
    """打印资产贡献明细"""
    asset_pnl = engine.get_asset_pnl()
    if not asset_pnl.empty:
        print("\n资产贡献明细:")
        for _, row in asset_pnl.iterrows():
            print(f"  {row['asset']}: {row['total_pnl']:+,.2f} ({row['contribution']:+.2%})")
        print(f"  合计贡献: {asset_pnl['contribution'].sum():.2%}")

def handle_update_data():
    """更新行业轮动资产池数据"""
    assets_to_update = list(SECTOR_ASSET_CODES.items())
    failed_assets = update_all_data(assets_to_update=assets_to_update)

    while failed_assets:
        print("\n请选择操作:")
        print("1. 重试失败的资产 (Retry)")
        print("2. 跳过，继续 (Skip)")

        retry_choice = input("请输入选项 (1-2): ").strip()

        if retry_choice == '2':
            break
        else:
            failed_assets = update_all_data(assets_to_update=failed_assets)

def strategy_menu(s):
    """策略子菜单：回测 / 优化 / 信号"""
    while True:
        print(f"\n--- {s['name']} ---")
        print("1. 运行回测")
        print("2. 优化参数")
        print("3. 获取实盘建议")
        print("0. 返回上级")

        choice = input("请选择 (0-3): ").strip()

        if choice == '1':
            params = s['params']()
            print(f"\n正在运行回测 (M={params['m']}, N={params['n']}, K={params['k']}, SL={params['stop_loss_pct']:.0%})...")
            data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
            engine = BacktestEngine(data_map=data_map)
            strategy = s['class'](**params)
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if not k.endswith("Ratio") else f"{v:.2f}"
                print(f"{k}: {val}")
            print_asset_pnl(engine)

        elif choice == '2':
            print(f"\n正在优化参数...")
            best_params, _ = s['optimize']()

        elif choice == '3':
            params = s['params']()
            print(f"\n正在获取实盘建议...")
            get_trading_signal(strategy_type=s['type'], **params, update=True)

        elif choice == '0':
            break
        else:
            print("无效选项，请重试。")

def main():
    while True:
        print("\n" + "="*30)
        print("   量化轮动策略系统")
        print("="*30)
        for key, s in STRATEGIES.items():
            print(f"{key}. {s['name']}")
        print(f"{len(STRATEGIES)+1}. 更新数据")
        print("0. 退出")
        print("="*30)

        choice = input("请选择策略或操作: ").strip()

        if choice in STRATEGIES:
            strategy_menu(STRATEGIES[choice])
        elif choice == str(len(STRATEGIES)+1):
            handle_update_data()
        elif choice == '0':
            print("退出系统。")
            sys.exit(0)
        else:
            print("无效选项，请重试。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已终止。")
        sys.exit(0)
