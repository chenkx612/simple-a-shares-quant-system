import sys
from src.data_loader import update_all_data
from src.backtest import BacktestEngine
from src.optimize import optimize_n
from src.trading_signal import get_trading_signal
from src.config import DEFAULT_N

def print_menu():
    print("\n" + "="*30)
    print("   个人量化投资系统   ")
    print("="*30)
    print("1. 更新数据 (Update Data)")
    print("2. 运行回测 (Run Backtest)")
    print("3. 优化参数 (Optimize Parameters)")
    print("4. 获取实盘建议 (Get Trading Signal)")
    print("0. 退出 (Exit)")
    print("="*30)

def main():
    while True:
        print_menu()
        choice = input("请输入选项 (0-4): ").strip()
        
        if choice == '1':
            print("\n正在更新数据...")
            update_all_data()
            print("数据更新完成。")
            
        elif choice == '2':
            print(f"\n正在运行回测 (N={DEFAULT_N})...")
            engine = BacktestEngine()
            strategy = MomentumStrategy(portfolios=PORTFOLIOS, n=DEFAULT_N)
            engine.run(strategy)
            metrics = engine.get_metrics()
            print("\n回测结果:")
            for k, v in metrics.items():
                val = f"{v:.2%}" if k != "Sharpe Ratio" else f"{v:.2f}"
                print(f"{k}: {val}")
                
        elif choice == '3':
            print("\n正在优化参数...")
            best_n, _ = optimize_n()
            print(f"\n建议: 请手动更新 src/config.py 中的 DEFAULT_N = {best_n}")
            
        elif choice == '4':
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
