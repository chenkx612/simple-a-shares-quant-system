import sys
from src.data_loader import update_all_data, load_all_data
from src.backtest import BacktestEngine
from src.optimize import optimize_sector_params
from src.trading_signal import get_trading_signal
from src.config import (
    SECTOR_ASSET_CODES, SECTOR_M, SECTOR_N, SECTOR_K, SECTOR_CORR_THRESHOLD, SECTOR_STOP_LOSS_PCT,
)
from src.strategy import SectorRotationStrategy

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
    print("\n[行业轮动资产池] 正在更新数据...")
    print("(已是最新的资产将自动跳过)")

    assets_to_update = list(SECTOR_ASSET_CODES.items())
    failed_assets = update_all_data(assets_to_update=assets_to_update)

    # 处理失败重试
    while failed_assets:
        print(f"\n警告: 以下 {len(failed_assets)} 个资产更新失败:")
        for name, code in failed_assets:
            print(f"  - {name} ({code})")

        print("\n请选择操作:")
        print("1. 重试失败的资产 (Retry)")
        print("2. 跳过，继续 (Skip)")

        retry_choice = input("请输入选项 (1-2): ").strip()

        if retry_choice == '2':
            print("跳过失败资产。")
            break
        else:
            print("\n正在重试...")
            failed_assets = update_all_data(assets_to_update=failed_assets)

    if not failed_assets:
        print("\n数据更新完成。")
    else:
        print(f"\n数据更新完成，但有 {len(failed_assets)} 个资产更新失败。")

def main():
    while True:
        print("\n" + "="*30)
        print("   行业轮动策略 (Sector Rotation)   ")
        print("="*30)
        print("1. 运行回测 (Run Backtest)")
        print("2. 优化参数 (Optimize Params)")
        print("3. 获取实盘建议 (Get Trading Signal)")
        print("4. 更新数据 (Update Data)")
        print("0. 退出 (Exit)")
        print("="*30)

        choice = input("请输入选项 (0-4): ").strip()

        if choice == '1':
            print(f"\n正在运行行业轮动策略回测 (M={SECTOR_M}, N={SECTOR_N}, K={SECTOR_K}, SL={SECTOR_STOP_LOSS_PCT:.0%})...")
            data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
            engine = BacktestEngine(data_map=data_map)
            strategy = SectorRotationStrategy(
                m=SECTOR_M, n=SECTOR_N, k=SECTOR_K,
                corr_threshold=SECTOR_CORR_THRESHOLD, stop_loss_pct=SECTOR_STOP_LOSS_PCT
            )
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if not k.endswith("Ratio") else f"{v:.2f}"
                print(f"{k}: {val}")
            print_asset_pnl(engine)

        elif choice == '2':
            print("\n正在优化行业轮动参数...")
            best_params, _ = optimize_sector_params()
            if best_params:
                print(f"\n建议: 请手动更新 src/config.py 中的 SECTOR_M = {best_params['m']}, SECTOR_N = {best_params['n']}, SECTOR_STOP_LOSS_PCT = {best_params['stop_loss_pct']}")

        elif choice == '3':
             print("\n正在获取实盘建议...")
             get_trading_signal(
                 strategy_type='sector_rotation',
                 m=SECTOR_M, n=SECTOR_N, k=SECTOR_K,
                 corr_threshold=SECTOR_CORR_THRESHOLD, stop_loss_pct=SECTOR_STOP_LOSS_PCT,
                 update=True
             )

        elif choice == '4':
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
