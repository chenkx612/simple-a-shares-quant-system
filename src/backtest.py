import pandas as pd
import numpy as np
from .config import PORTFOLIOS, DEFAULT_N, START_DATE, COMMISSION_RATE
from .data_loader import load_all_data

class BacktestEngine:
    def __init__(self, start_date=START_DATE):
        self.start_date = start_date
        self.data_map = load_all_data()
        self.aligned_close = self._align_data('close')
        self.aligned_open = self._align_data('open')
        self.daily_returns_close = self.aligned_close.pct_change().fillna(0)
        self.daily_returns_open = self.aligned_open.pct_change().fillna(0)
        
    def _align_data(self, price_col='close'):
        # Merge all prices into one DF
        dfs = []
        for asset_key, df in self.data_map.items():
            if price_col in df.columns:
                s = df[price_col].rename(asset_key)
                dfs.append(s)
            else:
                print(f"Warning: '{price_col}' column missing for {asset_key}")
        
        if not dfs:
            raise ValueError(f"No data loaded for {price_col}")
            
        combined = pd.concat(dfs, axis=1)
        combined = combined.sort_index()
        # Forward fill for missing data (e.g. non-trading days for some markets)
        combined = combined.ffill()
        # Filter by start_date
        combined = combined[combined.index >= self.start_date]
        return combined

    def calculate_portfolio_returns(self, daily_returns=None):
        """
        Calculate daily returns for each strategy portfolio
        """
        if daily_returns is None:
            daily_returns = self.daily_returns_close

        port_rets = pd.DataFrame(index=daily_returns.index)
        
        for p_key, p_val in PORTFOLIOS.items():
            p_ret = pd.Series(0.0, index=daily_returns.index)
            valid_asset = False
            for asset, weight in p_val['assets'].items():
                if asset in daily_returns.columns:
                    p_ret += daily_returns[asset] * weight
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
        # 1. Portfolio Daily Returns (Close-to-Close for Signal)
        port_daily_rets_close = self.calculate_portfolio_returns(self.daily_returns_close)
        
        # 2. Strategy Signal (based on Close prices)
        # Construct wealth index for each portfolio to calculate n-day return correctly
        # (1+r1)*(1+r2)...
        port_wealth = (1 + port_daily_rets_close).cumprod()
        
        # Past n days return = Wealth_T / Wealth_{T-n} - 1
        past_n_returns = port_wealth / port_wealth.shift(n) - 1
        
        # Signal: Select portfolio with max past_n_return
        # idxmax gives the column name with max value
        signal = past_n_returns.idxmax(axis=1)
        
        # 3. Strategy Performance (based on Open prices)
        # Execute at Open, so we track Open-to-Open returns
        port_daily_rets_open = self.calculate_portfolio_returns(self.daily_returns_open)
        
        # Strategy holds 'signal' from previous day(s)
        # If signal generated at Close(T-2), we trade at Open(T-1).
        # We hold from Open(T-1) to Open(T).
        # The return (Open(T)-Open(T-1))/Open(T-1) is at index T.
        # So at index T, we use Signal(T-2).
        active_signal = signal.shift(2)
        
        strategy_ret = pd.Series(0.0, index=port_daily_rets_open.index)
        
        for p_key in PORTFOLIOS.keys():
            mask = (active_signal == p_key)
            strategy_ret[mask] = port_daily_rets_open[p_key][mask]
            
        # 4. Apply Transaction Costs (Commission)
        # Calculate when trades occur
        prev_signal = active_signal.shift(1)
        
        # Entry: transitioning from NaN (no position) to a valid signal
        # Note: signal has NaNs at the beginning due to shift(2) and past_n_returns
        entry_mask = (prev_signal.isna()) & (active_signal.notna())
        
        # Switch: transitioning from one valid signal to another valid signal
        switch_mask = (prev_signal.notna()) & (active_signal.notna()) & (prev_signal != active_signal)
        
        # Cost application
        costs = pd.Series(0.0, index=strategy_ret.index)
        
        # Entry cost: buy new portfolio (1x commission)
        costs[entry_mask] = COMMISSION_RATE
        
        # Switch cost: sell old portfolio + buy new portfolio (2x commission)
        costs[switch_mask] = 2 * COMMISSION_RATE
        
        # Adjust returns: R_net = (1 + R_gross) * (1 - cost) - 1
        strategy_ret = (1 + strategy_ret) * (1 - costs) - 1
            
        return strategy_ret, active_signal, port_daily_rets_open

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
        rf = 0.011
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
