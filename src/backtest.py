import pandas as pd
import numpy as np
from .config import START_DATE, COMMISSION_RATE, DATA_DIR
from .data_loader import load_all_data
from .strategy import Strategy

class BacktestEngine:
    def __init__(self, initial_capital=100000.0, commission_rate=COMMISSION_RATE, start_date=START_DATE):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.start_date = pd.Timestamp(start_date)
        
        self.data_map = load_all_data()
        self.aligned_open = None
        self.aligned_close = None
        self.available_assets = []
        
        self._prepare_data()
        
        # Account State
        self.cash = initial_capital
        self.positions = {} # {asset_code: shares}
        self.history = [] # List of dicts recording daily state

    def _prepare_data(self):
        """
        Align data for all assets
        """
        opens = []
        closes = []
        
        for asset, df in self.data_map.items():
            if 'open' in df.columns and 'close' in df.columns:
                opens.append(df['open'].rename(asset))
                closes.append(df['close'].rename(asset))
                
        if not opens:
            raise ValueError("No valid data found")
            
        self.aligned_open = pd.concat(opens, axis=1).sort_index().ffill()
        self.aligned_close = pd.concat(closes, axis=1).sort_index().ffill()
        
        # Filter by start date
        self.aligned_open = self.aligned_open[self.aligned_open.index >= self.start_date]
        self.aligned_close = self.aligned_close[self.aligned_close.index >= self.start_date]
        
        self.available_assets = self.aligned_open.columns.tolist()

    def run(self, strategy: Strategy):
        """
        Run the backtest loop
        """
        # Pass data to strategy
        # Note: Strategy needs access to historical data. 
        # For simplicity, we pass the raw map. 
        # Strategy is responsible for looking at data only up to 'date'.
        strategy.set_data(self.data_map, self.aligned_open.index)
        
        print(f"Starting backtest from {self.aligned_open.index[0]} to {self.aligned_open.index[-1]}...")
        
        for date in self.aligned_open.index:
            # 1. Get Market Data for today
            try:
                open_prices = self.aligned_open.loc[date]
                close_prices = self.aligned_close.loc[date]
            except KeyError:
                continue
                
            # 2. Strategy Step (Generate Signal based on history up to yesterday)
            # The strategy returns target weights for TODAY (to be executed at Open)
            target_weights = strategy.get_target_weights(date)
            
            # 3. Execute Trades at Open
            self._rebalance(target_weights, open_prices)
            
            # 4. Update Portfolio Value at Close
            total_value = self._calculate_total_value(close_prices)
            
            # 5. Record History
            self.history.append({
                'date': date,
                'total_value': total_value,
                'cash': self.cash,
                'positions': self.positions.copy()
            })
            
        return pd.DataFrame(self.history).set_index('date')

    def _rebalance(self, target_weights, current_prices):
        """
        Rebalance portfolio to target weights at current prices.
        """
        # Calculate current total equity using OPEN prices (execution price)
        current_equity = self._calculate_total_value(current_prices)
        
        if current_equity <= 0:
            return

        # If no target, liquidate everything
        if not target_weights:
            for asset, shares in list(self.positions.items()):
                if shares > 0:
                    price = current_prices.get(asset, 0)
                    if price > 0:
                        value = shares * price
                        cost = value * self.commission_rate
                        self.cash += value - cost
                        self.positions[asset] = 0
            return

        # Calculate target value for each asset
        # target_weights: {asset: weight}
        
        # First, handle sells to free up cash
        # We need to know how much to buy/sell
        # Target Value = Total Equity * Weight
        
        # Note: This is a simplified "Target Weight" execution.
        # Real execution might be more complex (ordering sells before buys, etc.)
        # Here we calculate net change in cash required.
        
        # But wait, transaction cost reduces equity.
        # If we target 100% equity, we might run out of cash due to commissions.
        # We should reserve some cash or adjust weights?
        # For simplicity, we assume weights sum to 1.0 or less.
        # If sum is 1.0, we might need to sell slightly more or buy slightly less.
        # Let's calculate target shares.
        
        # To avoid complex solving for exact commission, we approximate:
        # We use current_equity as the basis.
        
        for asset, weight in target_weights.items():
            if asset not in current_prices or pd.isna(current_prices[asset]):
                continue
                
            target_val = current_equity * weight
            price = current_prices[asset]
            
            if price <= 0: continue
            
            target_shares = target_val / price
            current_shares = self.positions.get(asset, 0)
            
            diff_shares = target_shares - current_shares
            
            if diff_shares == 0:
                continue
                
            trade_val = diff_shares * price
            cost = abs(trade_val) * self.commission_rate
            
            # Update
            self.cash -= (trade_val + cost)
            self.positions[asset] = current_shares + diff_shares

        # Handle assets that are not in target_weights (Sell them)
        for asset in list(self.positions.keys()):
            if asset not in target_weights and self.positions[asset] > 0:
                price = current_prices.get(asset, 0)
                if price > 0:
                    shares = self.positions[asset]
                    value = shares * price
                    cost = value * self.commission_rate
                    self.cash += value - cost
                    self.positions[asset] = 0

    def _calculate_total_value(self, prices):
        val = self.cash
        for asset, shares in self.positions.items():
            if shares != 0:
                price = prices.get(asset, 0)
                if not pd.isna(price):
                    val += shares * price
        return val

    def get_metrics(self):
        if not self.history:
            return {}
            
        df = pd.DataFrame(self.history).set_index('date')
        df['returns'] = df['total_value'].pct_change().fillna(0)
        
        total_ret = (df['total_value'].iloc[-1] / self.initial_capital) - 1
        days = len(df)
        ann_ret = (1 + total_ret) ** (252/days) - 1
        
        rf = 0.02
        vol = df['returns'].std() * np.sqrt(252)
        sharpe = (ann_ret - rf) / vol if vol != 0 else 0
        
        # Max Drawdown
        wealth = df['total_value']
        peak = wealth.cummax()
        drawdown = (wealth - peak) / peak
        max_dd = drawdown.min()
        
        return {
            "Total Return": total_ret,
            "Annualized Return": ann_ret,
            "Sharpe Ratio": sharpe,
            "Max Drawdown": max_dd,
            "Volatility": vol
        }

if __name__ == "__main__":
    from .strategy import MomentumStrategy
    from .config import PORTFOLIOS, DEFAULT_N
    
    engine = BacktestEngine()
    strategy = MomentumStrategy(portfolios=PORTFOLIOS, n=DEFAULT_N)
    
    result = engine.run(strategy)
    metrics = engine.get_metrics()
    
    print("\nBacktest Results:")
    for k, v in metrics.items():
        print(f"{k}: {v:.2%}" if k != "Sharpe Ratio" else f"{k}: {v:.2f}")
