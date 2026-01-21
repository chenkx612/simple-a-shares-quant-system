import pandas as pd
import numpy as np
from .config import PORTFOLIOS, DEFAULT_N, START_DATE, ASSET_CODES
from .data_loader import load_all_data

class BacktestEngine:
    def __init__(self, start_date=START_DATE):
        self.start_date = start_date
        self.data_map = load_all_data()
        self.aligned_data = self._align_data()
        self.daily_returns = self.aligned_data.pct_change().fillna(0)
        
    def _align_data(self):
        # Merge all closes into one DF
        dfs = []
        for asset_key, df in self.data_map.items():
            # Use 'close' price
            if 'close' in df.columns:
                s = df['close'].rename(asset_key)
                dfs.append(s)
            else:
                print(f"Warning: 'close' column missing for {asset_key}")
        
        if not dfs:
            raise ValueError("No data loaded")
            
        combined = pd.concat(dfs, axis=1)
        combined = combined.sort_index()
        # Forward fill for missing data (e.g. non-trading days for some markets)
        combined = combined.ffill()
        # Filter by start_date
        combined = combined[combined.index >= self.start_date]
        return combined

    def calculate_portfolio_returns(self):
        """
        Calculate daily returns for each strategy portfolio
        """
        port_rets = pd.DataFrame(index=self.daily_returns.index)
        
        for p_key, p_val in PORTFOLIOS.items():
            p_ret = pd.Series(0.0, index=self.daily_returns.index)
            valid_asset = False
            for asset, weight in p_val['assets'].items():
                # ASSET_CODES keys map to data_map keys?
                # In config.py: ASSET_CODES = {"kc50": "588000", ...}
                # In data_loader.py: load_all_data uses ASSET_CODES keys as keys in data_map
                # So asset string like "kc50" should be in self.daily_returns.columns
                
                if asset in self.daily_returns.columns:
                    p_ret += self.daily_returns[asset] * weight
                    valid_asset = True
                else:
                    print(f"Warning: Asset {asset} not in daily returns")
            
            if valid_asset:
                port_rets[p_key] = p_ret
            
        return port_rets

    def run_strategy(self, n=DEFAULT_N):
        """
        Run the strategy with parameter n
        """
        # 1. Portfolio Daily Returns
        port_daily_rets = self.calculate_portfolio_returns()
        
        # 2. Strategy Signal
        # Construct wealth index for each portfolio to calculate n-day return correctly
        # (1+r1)*(1+r2)...
        port_wealth = (1 + port_daily_rets).cumprod()
        
        # Past n days return = Wealth_T / Wealth_{T-n} - 1
        past_n_returns = port_wealth / port_wealth.shift(n) - 1
        
        # Signal: Select portfolio with max past_n_return
        # idxmax gives the column name with max value
        signal = past_n_returns.idxmax(axis=1)
        
        # 3. Strategy Performance
        # Strategy holds 'signal' from previous day
        # shift(1) moves signal from T to T+1
        active_signal = signal.shift(1)
        
        strategy_ret = pd.Series(0.0, index=port_daily_rets.index)
        
        for p_key in PORTFOLIOS.keys():
            mask = (active_signal == p_key)
            strategy_ret[mask] = port_daily_rets[p_key][mask]
            
        return strategy_ret, active_signal, port_daily_rets

    @staticmethod
    def calculate_metrics(returns):
        # Annualized Return, Sharpe, Max Drawdown
        if returns.empty:
            return {}
            
        # Clean NaN (first few days)
        returns = returns.dropna()
        if len(returns) == 0: return {}

        total_ret = (1 + returns).prod() - 1
        days = len(returns)
        
        # Annualized Return
        ann_ret = (1 + total_ret) ** (252/days) - 1
        
        # Sharpe Ratio (assuming Risk Free Rate = 2%)
        rf = 0.02
        vol = returns.std() * np.sqrt(252)
        sharpe = (ann_ret - rf) / vol if vol != 0 else 0
        
        # Max Drawdown
        wealth = (1 + returns).cumprod()
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
    engine = BacktestEngine()
    ret, sig, port_rets = engine.run_strategy(n=20)
    metrics = engine.calculate_metrics(ret)
    
    print("Strategy Performance (N=20):")
    for k, v in metrics.items():
        print(f"{k}: {v:.2%}" if k != "Sharpe Ratio" else f"{k}: {v:.2f}")
