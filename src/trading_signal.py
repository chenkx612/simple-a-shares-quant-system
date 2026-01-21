from .config import PORTFOLIOS, DEFAULT_N, ASSET_CODES
from .data_loader import update_all_data
from .backtest import BacktestEngine

def get_trading_signal(n=DEFAULT_N, update=True):
    if update:
        user_input = input("是否更新数据? (y/n, 默认 n): ").strip().lower()
        if user_input == 'y':
            print("Updating data...")
            update_all_data()
        else:
            print("Skipping data update.")
        
    engine = BacktestEngine(start_date="20250101") # Only load recent data for speed
    
    # Calculate portfolio daily returns
    port_rets = engine.calculate_portfolio_returns()
    
    # We need the last n+1 days to calculate n-day return
    # If today is T, we need Price_T and Price_{T-n}
    # Return = Price_T / Price_{T-n} - 1
    
    # Get wealth index
    wealth = (1 + port_rets).cumprod()
    
    if len(wealth) < n + 1:
        print("Not enough data to calculate signal.")
        return

    # Calculate n-day return for the last available day
    # We look at the last row of wealth, and the row n days before it
    
    last_date = wealth.index[-1]
    prev_n_date_idx = -1 - n
    
    if abs(prev_n_date_idx) > len(wealth):
         print("Not enough data history.")
         return

    current_wealth = wealth.iloc[-1]
    prev_wealth = wealth.iloc[prev_n_date_idx]
    
    # Return over past n days
    n_day_returns = current_wealth / prev_wealth - 1
    
    # Sort
    sorted_rets = n_day_returns.sort_values(ascending=False)
    
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
