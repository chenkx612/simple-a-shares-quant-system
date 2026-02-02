import sys
from src.data_loader import update_all_data
from src.backtest import BacktestEngine
from src.optimize import optimize_smart_params, optimize_stop_loss_params
from src.trading_signal import get_trading_signal
from src.config import SMART_M, SMART_N, SMART_K, CORR_THRESHOLD, STOP_LOSS_M, STOP_LOSS_N, STOP_LOSS_K, STOP_LOSS_CORR_THRESHOLD, STOP_LOSS_PCT
from src.strategy import SmartRotationStrategy, StopLossRotationStrategy

def handle_update_data():
    print("\n请选择更新模式:")
    print("1. 增量更新 (Incremental Update) - 仅更新最新数据，速度快")
    print("2. 全量更新 (Full Update) - 重新拉取所有历史数据，修正复权误差")

    choice = input("请输入选项 (1-2): ").strip()

    if choice == '1':
        print("\n正在进行增量更新...")
        force_full = False
    elif choice == '2':
        print("\n正在进行全量更新...")
        force_full = True
    else:
        print("无效选项，取消更新。")
        return

    failed_assets = update_all_data(force_full=force_full)

    # 处理失败重试
    while failed_assets:
        print(f"\n警告: 以下 {len(failed_assets)} 个资产更新失败:")
        for name, code in failed_assets:
            print(f"  - {name} ({code})")

        print("\n请选择操作:")
        print("1. 重试失败的资产 (Retry)")
        print("2. 跳过，继续 (Skip)")

        retry_choice = input("请输入选项 (1-2): ").strip()

        if retry_choice == '1':
            print("\n正在重试...")
            failed_assets = update_all_data(force_full=force_full, assets_to_update=failed_assets)
        else:
            print("跳过失败资产。")
            break

    if not failed_assets:
        print("\n数据更新完成。")
    else:
        print(f"\n数据更新完成，但有 {len(failed_assets)} 个资产更新失败。")

def smart_rotation_menu():
    while True:
        print("\n" + "="*30)
        print("   智能轮动策略 (Smart Rotation)   ")
        print("="*30)
        print("1. 运行回测 (Run Backtest)")
        print("2. 优化参数 (Optimize Params)")
        print("3. 获取实盘建议 (Get Trading Signal)")
        print("4. 更新数据 (Update Data)")
        print("0. 返回主菜单 (Back)")
        print("="*30)
        
        choice = input("请输入选项 (0-4): ").strip()
        
        if choice == '1':
            print(f"\n正在运行智能轮动策略回测 (M={SMART_M}, N={SMART_N}, K={SMART_K})...")
            engine = BacktestEngine()
            strategy = SmartRotationStrategy(m=SMART_M, n=SMART_N, k=SMART_K, corr_threshold=CORR_THRESHOLD)
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if k != "Sharpe Ratio" else f"{v:.2f}"
                print(f"{k}: {val}")
        
        elif choice == '2':
            print("\n正在优化智能轮动参数...")
            best_params, _ = optimize_smart_params()
            print(f"\n建议: 请手动更新 src/config.py 中的 SMART_M = {best_params[0]}, SMART_N = {best_params[1]}")
            
        elif choice == '3':
             print("\n正在获取实盘建议...")
             get_trading_signal(strategy_type='smart_rotation', m=SMART_M, n=SMART_N, k=SMART_K, corr_threshold=CORR_THRESHOLD, update=True)

        elif choice == '4':
            handle_update_data()
            
        elif choice == '0':
            break
        else:
            print("无效选项，请重试。")

def stop_loss_rotation_menu():
    while True:
        print("\n" + "="*30)
        print("   止损轮动策略 (Stop Loss Rotation)   ")
        print("="*30)
        print("1. 运行回测 (Run Backtest)")
        print("2. 优化参数 (Optimize Params)")
        print("3. 获取实盘建议 (Get Trading Signal)")
        print("4. 更新数据 (Update Data)")
        print("0. 返回主菜单 (Back)")
        print("="*30)

        choice = input("请输入选项 (0-4): ").strip()

        if choice == '1':
            print(f"\n正在运行止损轮动策略回测 (M={STOP_LOSS_M}, N={STOP_LOSS_N}, K={STOP_LOSS_K}, SL={STOP_LOSS_PCT:.0%})...")
            engine = BacktestEngine()
            strategy = StopLossRotationStrategy(
                m=STOP_LOSS_M, n=STOP_LOSS_N, k=STOP_LOSS_K,
                corr_threshold=STOP_LOSS_CORR_THRESHOLD, stop_loss_pct=STOP_LOSS_PCT
            )
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if k != "Sharpe Ratio" else f"{v:.2f}"
                print(f"{k}: {val}")

        elif choice == '2':
            print("\n正在优化止损轮动参数...")
            best_params, _ = optimize_stop_loss_params()
            print(f"\n建议: 请手动更新 src/config.py 中的 STOP_LOSS_M = {best_params[0]}, STOP_LOSS_N = {best_params[1]}, STOP_LOSS_PCT = {best_params[2]}")

        elif choice == '3':
             print("\n正在获取实盘建议...")
             get_trading_signal(
                 strategy_type='stop_loss_rotation',
                 m=STOP_LOSS_M, n=STOP_LOSS_N, k=STOP_LOSS_K,
                 corr_threshold=STOP_LOSS_CORR_THRESHOLD, stop_loss_pct=STOP_LOSS_PCT,
                 update=True
             )

        elif choice == '4':
            handle_update_data()

        elif choice == '0':
            break
        else:
            print("无效选项，请重试。")

def main():
    while True:
        print("\n" + "="*30)
        print("   个人量化投资系统   ")
        print("="*30)
        print("1. 智能轮动策略 (Smart Rotation)")
        print("2. 止损轮动策略 (Stop Loss Rotation)")
        print("3. 更新数据 (Update All Data)")
        print("0. 退出 (Exit)")
        print("="*30)

        choice = input("请输入选项 (0-3): ").strip()

        if choice == '1':
            smart_rotation_menu()
        elif choice == '2':
            stop_loss_rotation_menu()
        elif choice == '3':
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
