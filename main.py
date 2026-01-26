import sys
from src.data_loader import update_all_data
from src.backtest import BacktestEngine
from src.optimize import optimize_n, optimize_smart_params
from src.trading_signal import get_trading_signal
from src.config import DEFAULT_N, PORTFOLIOS, SMART_M, SMART_N, SMART_K, CORR_THRESHOLD
from src.strategy import MomentumStrategy, SmartRotationStrategy

def print_menu():
    print("\n" + "="*30)
    print("   个人量化投资系统   ")
    print("="*30)
    print("1. 更新数据 (Update Data)")
    print("2. 运行动量策略回测 (Run Momentum Backtest)")
    print("3. 运行智能轮动策略回测 (Run Smart Rotation Backtest)")
    print("4. 优化动量参数 (Optimize Momentum Params)")
    print("5. 优化智能轮动参数 (Optimize Smart Rotation Params)")
    print("6. 获取实盘建议 (Get Trading Signal)")
    print("0. 退出 (Exit)")
    print("="*30)

def main():
    while True:
        print_menu()
        choice = input("请输入选项 (0-6): ").strip()
        
        if choice == '1':
            print("\n正在更新数据...")
            update_all_data()
            print("数据更新完成。")
            
        elif choice == '2':
            print(f"\n正在运行动量策略回测 (N={DEFAULT_N})...")
            engine = BacktestEngine()
            strategy = MomentumStrategy(portfolios=PORTFOLIOS, n=DEFAULT_N)
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if k != "Sharpe Ratio" else f"{v:.2f}"
                print(f"{k}: {val}")
        
        elif choice == '3':
            print(f"\n正在运行智能轮动策略回测 (M={SMART_M}, N={SMART_N}, K={SMART_K})...")
            engine = BacktestEngine()
            strategy = SmartRotationStrategy(m=SMART_M, n=SMART_N, k=SMART_K, corr_threshold=CORR_THRESHOLD)
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if k != "Sharpe Ratio" else f"{v:.2f}"
                print(f"{k}: {val}")
                
        elif choice == '4':
            print("\n正在优化参数...")
            best_n, _ = optimize_n()
            print(f"\n建议: 请手动更新 src/config.py 中的 DEFAULT_N = {best_n}")
            
        elif choice == '5':
            print("\n正在优化智能轮动参数...")
            best_params, _ = optimize_smart_params()
            print(f"\n建议: 请手动更新 src/config.py 中的 SMART_M = {best_params[0]}, SMART_N = {best_params[1]}")
            
        elif choice == '6':
            print("\n正在获取实盘建议...")
            # 默认更新数据以确保信号最新
            get_trading_signal(n=DEFAULT_N, update=True)
            
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
