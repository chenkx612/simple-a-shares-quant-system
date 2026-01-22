from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class Strategy(ABC):
    def __init__(self):
        self.data_map = None
        self.dates = None
        
    def set_data(self, data_map, dates):
        """
        Set the data for the strategy.
        data_map: dict of {asset_code: dataframe}
        dates: list/index of dates to run
        """
        self.data_map = data_map
        self.dates = dates
        self.on_data_loaded()

    def on_data_loaded(self):
        """
        Hook to perform pre-calculations after data is loaded.
        """
        pass

    @abstractmethod
    def get_target_weights(self, date):
        """
        Return the target weights for the given date.
        The backtester will call this BEFORE market open to determine trades for the day.
        
        Args:
            date: The current date (timestamp)
            
        Returns:
            dict: {asset_code: target_weight} (sum should be <= 1.0)
        """
        pass

class MomentumStrategy(Strategy):
    def __init__(self, portfolios, n=20):
        super().__init__()
        self.portfolios = portfolios
        self.n = n
        self.signals = None # Series indexed by date, value is portfolio key
        
    def on_data_loaded(self):
        # 1. Align Close Prices
        dfs = []
        for asset_key, df in self.data_map.items():
            if 'close' in df.columns:
                s = df['close'].rename(asset_key)
                dfs.append(s)
        
        if not dfs:
            return
            
        prices = pd.concat(dfs, axis=1).sort_index().ffill()
        
        # 2. Calculate Portfolio Curves (Wealth Index)
        # We need daily returns to calculate wealth
        daily_rets = prices.pct_change().fillna(0)
        
        self.port_wealth = pd.DataFrame(index=daily_rets.index)
        
        for p_key, p_val in self.portfolios.items():
            p_ret = pd.Series(0.0, index=daily_rets.index)
            for asset, weight in p_val['assets'].items():
                if asset in daily_rets.columns:
                    p_ret += daily_rets[asset] * weight
            
            # Wealth index = cumprod(1 + r)
            self.port_wealth[p_key] = (1 + p_ret).cumprod()
            
        # 3. Calculate Momentum (Past N days return)
        # Return = Wealth_T / Wealth_{T-n} - 1
        self.past_n_returns = self.port_wealth / self.port_wealth.shift(self.n) - 1
        
        # 4. Generate Signals
        # Signal T is based on data up to T.
        # It will be used for trading on T+1 Open.
        # In the original code: signal = past_n_returns.idxmax(axis=1)
        # Handle all-NaN rows to avoid FutureWarning
        self.signals = pd.Series(index=self.past_n_returns.index, dtype='object')
        
        # Only calculate idxmax for rows that have at least one valid value
        valid_rows = self.past_n_returns.notna().any(axis=1)
        if valid_rows.any():
            self.signals.loc[valid_rows] = self.past_n_returns.loc[valid_rows].idxmax(axis=1)

    def get_target_weights(self, date):
        # We need the signal generated BEFORE today (i.e., yesterday's close)
        # Find the location of date
        if self.signals is None or date not in self.signals.index:
            return {}
            
        # Get integer location
        try:
            loc = self.signals.index.get_loc(date)
        except KeyError:
            return {}
            
        if loc == 0:
            return {}
            
        # The signal to use today (Open) was generated yesterday (Close)
        # signal_date = self.signals.index[loc - 1]
        # target_portfolio = self.signals.loc[signal_date]
        
        # Wait, if we use shift(2) logic from original code:
        # Original: active_signal = signal.shift(2)
        # Return at T uses signal.shift(2) -> Signal(T-2)
        # Return at T is Open(T) - Open(T-1).
        # This implies we entered at Open(T-1) using Signal(T-2).
        
        # In this function `get_target_weights(date)`:
        # It is called at `date` (Open). We are about to trade.
        # If this is Open(T), we want to establish the position for the day T.
        # Wait, if we want to reproduce the original logic:
        # Original: Return T (Open-to-Open) depends on Signal T-2.
        # Means: At Open(T-1), we used Signal(T-2).
        # So at Open(T), we should use Signal(T-1).
        
        # So here, for `date` (which is T), we need Signal(T-1).
        
        prev_signal = self.signals.iloc[loc - 1]
        
        if pd.isna(prev_signal):
            return {}
            
        if prev_signal not in self.portfolios:
            return {}
            
        return self.portfolios[prev_signal]['assets']
