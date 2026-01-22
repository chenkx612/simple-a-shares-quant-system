from .config import PORTFOLIOS, DEFAULT_N, ASSET_CODES
from .data_loader import update_all_data
from .backtest import BacktestEngine
from .strategy import MomentumStrategy

def get_trading_signal(n=DEFAULT_N, update=True):
    if update:
        user_input = input("是否更新数据? (y/n, 默认 n): ").strip().lower()
        if user_input == 'y':
            print("Updating data...")
            update_all_data()
        else:
            print("Skipping data update.")
        
    engine = BacktestEngine(start_date="20240101") # Use a reasonable lookback
    strategy = MomentumStrategy(portfolios=PORTFOLIOS, n=n)
    
    # Initialize strategy data (calculates wealth and momentum)
    strategy.set_data(engine.data_map, engine.aligned_open.index)
    
    if strategy.past_n_returns is None or strategy.past_n_returns.empty:
        print("Not enough data to calculate signal.")
        return

    # Get the latest returns
    # past_n_returns is (Wealth_T / Wealth_{T-n} - 1)
    last_returns = strategy.past_n_returns.iloc[-1]
    last_date = strategy.past_n_returns.index[-1]
    
    if last_returns.isna().all():
         print(f"Not enough data history (Last date: {last_date}).")
         return
    
    # Sort
    sorted_rets = last_returns.sort_values(ascending=False)
    best_portfolio = sorted_rets.index[0]
    
    print("\n" + "="*50)
    print(f"TRADING SIGNAL for Next Trading Day")
    print(f"Data Date: {last_date.strftime('%Y-%m-%d')}")
    print(f"Lookback Window (N): {n} days")
    print("="*50)
    
    print(f"\nPortfolio Returns (Past {n} days):")
    for p, r in sorted_rets.items():
        p_name = PORTFOLIOS[p]['name']
        print(f"  {p_name:<20}: {r:>7.2%}")
        
    print("-" * 50)
    print(f"RECOMMENDATION: {PORTFOLIOS[best_portfolio]['name']}")
    print("-" * 50)
    
    # Details of the recommended portfolio
    print("\nTarget Allocation:")
    assets = PORTFOLIOS[best_portfolio]['assets']
    for asset, weight in assets.items():
        code = ASSET_CODES.get(asset, "N/A")
        print(f"  {asset:<10} ({code:<6}): {weight:.0%}")

        
if __name__ == "__main__":
    get_trading_signal()
