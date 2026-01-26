import sys
from src.data_loader import update_all_data
from src.backtest import BacktestEngine
from src.optimize import optimize_n, optimize_smart_params
from src.trading_signal import get_trading_signal
from src.config import DEFAULT_N, PORTFOLIOS, SMART_M, SMART_N, SMART_K, CORR_THRESHOLD
from src.strategy import MomentumStrategy, SmartRotationStrategy

def handle_update_data():
    print("\n请选择更新模式:")
    print("1. 增量更新 (Incremental Update) - 仅更新最新数据，速度快")
    print("2. 全量更新 (Full Update) - 重新拉取所有历史数据，修正复权误差")
    
    choice = input("请输入选项 (1-2): ").strip()
    
    if choice == '1':
        print("\n正在进行增量更新...")
        update_all_data(force_full=False)
    elif choice == '2':
        print("\n正在进行全量更新...")
        update_all_data(force_full=True)
    else:
        print("无效选项，取消更新。")
        return

    print("数据更新完成。")

def momentum_menu():
    while True:
        print("\n" + "="*30)
        print("   动量策略 (Momentum Strategy)   ")
        print("="*30)
        print("1. 运行回测 (Run Backtest)")
        print("2. 优化参数 (Optimize Params)")
        print("3. 获取实盘建议 (Get Trading Signal)")
        print("4. 更新数据 (Update Data)")
        print("0. 返回主菜单 (Back)")
        print("="*30)
        
        choice = input("请输入选项 (0-4): ").strip()
        
        if choice == '1':
            print(f"\n正在运行动量策略回测 (N={DEFAULT_N})...")
            engine = BacktestEngine()
            strategy = MomentumStrategy(portfolios=PORTFOLIOS, n=DEFAULT_N)
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if k != "Sharpe Ratio" else f"{v:.2f}"
                print(f"{k}: {val}")
                
        elif choice == '2':
            print("\n正在优化参数...")
            best_n, _ = optimize_n()
            print(f"\n建议: 请手动更新 src/config.py 中的 DEFAULT_N = {best_n}")
            
        elif choice == '3':
             print("\n正在获取实盘建议...")
             get_trading_signal(strategy_type='momentum', n=DEFAULT_N, update=True)
             
        elif choice == '4':
            handle_update_data()
            
        elif choice == '0':
            break
        else:
            print("无效选项，请重试。")

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

def main():
    while True:
        print("\n" + "="*30)
        print("   个人量化投资系统   ")
        print("="*30)
        print("1. 动量策略 (Momentum Strategy)")
        print("2. 智能轮动策略 (Smart Rotation)")
        print("3. 更新数据 (Update All Data)")
        print("0. 退出 (Exit)")
        print("="*30)
        
        choice = input("请输入选项 (0-3): ").strip()
        
        if choice == '1':
            momentum_menu()
        elif choice == '2':
            smart_rotation_menu()
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
