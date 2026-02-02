from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

from .config import SECTOR_ASSET_CODES

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

class SmartRotationStrategy(Strategy):
    def __init__(self, m=2, n=20, k=20, corr_threshold=0.6):
        super().__init__()
        self.m = m
        self.n = n
        self.k = k
        self.corr_threshold = corr_threshold
        self.signals = {} # Date -> [selected_assets]

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
        
        # 2. Calculate Daily Returns
        daily_rets = prices.pct_change().fillna(0)
        
        # 3. Calculate Factor: Return / Volatility over past n days
        # Return = Price_T / Price_{T-n} - 1
        rolling_return = prices / prices.shift(self.n) - 1
        
        # Volatility: Standard deviation of daily returns over n days
        # We use daily std dev. (Not annualized, since it's for ranking)
        rolling_vol = daily_rets.rolling(self.n).std()
        
        # Factor = Return / Volatility
        # Handle division by zero/nan
        self.factors = rolling_return / rolling_vol.replace(0, np.nan)
        
        # 4. Calculate Rolling Correlations
        # rolling(k).corr() returns a MultiIndex DataFrame (Date, Asset) -> Asset
        rolling_corr = daily_rets.rolling(self.k).corr()
        
        # 5. Generate Signals
        start_idx = max(self.n, self.k)
        valid_dates = prices.index[start_idx:]
        
        for date in valid_dates:
            # Get factors for this date
            if date not in self.factors.index:
                continue
                
            day_factors = self.factors.loc[date].dropna()
            
            if day_factors.empty:
                continue
                
            # Sort by factor descending
            sorted_assets = day_factors.sort_values(ascending=False).index.tolist()
            
            selected = []
            
            # Get correlation matrix for this date
            try:
                curr_corr = rolling_corr.loc[date]
            except KeyError:
                continue
                
            for asset in sorted_assets:
                if len(selected) >= self.m:
                    break
                    
                # Check correlation with already selected
                is_correlated = False
                for selected_asset in selected:
                    # Check correlation
                    # curr_corr is a DataFrame/Matrix
                    if asset in curr_corr.index and selected_asset in curr_corr.columns:
                        c = curr_corr.loc[asset, selected_asset]
                        # Use absolute correlation? Or just positive?
                        # "Too high correlation" usually implies positive correlation.
                        # If they are negatively correlated, it's actually good for diversification.
                        # So we should check for positive correlation > threshold.
                        # Or abs(correlation) > threshold if we want to avoid any strong linear relationship?
                        # User said "correlation too high" (相关性过高), usually means close to 1.
                        # I'll use > threshold.
                        if c > self.corr_threshold:
                            is_correlated = True
                            break
                
                if not is_correlated:
                    selected.append(asset)
            
            self.signals[date] = selected

    def get_target_weights(self, date):
        # We need the signal generated BEFORE today (i.e., yesterday's close)
        if self.dates is None:
             return {}
             
        try:
            # self.dates is expected to be a DatetimeIndex
            idx = self.dates.get_loc(date)
        except (ValueError, KeyError):
            return {}
            
        if idx == 0:
            return {}
            
        prev_date = self.dates[idx - 1]
        
        if prev_date in self.signals:
            selected = self.signals[prev_date]
            if not selected:
                return {}

            weight = 1.0 / len(selected)
            return {asset: weight for asset in selected}

        return {}

class StopLossRotationStrategy(Strategy):
    """
    止损轮动策略：在 SmartRotationStrategy 基础上增加止损机制。
    当某资产单日跌幅超过 stop_loss_pct，次日信号中排除该资产。
    """
    def __init__(self, m=3, n=30, k=100, corr_threshold=0.9, stop_loss_pct=0.05):
        super().__init__()
        self.m = m
        self.n = n
        self.k = k
        self.corr_threshold = corr_threshold
        self.stop_loss_pct = stop_loss_pct
        self.signals = {}  # Date -> [selected_assets]
        self.stopped_assets_log = {}  # Date -> set of stopped assets (for debugging)

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

        # 2. Calculate Daily Returns
        daily_rets = prices.pct_change().fillna(0)

        # 3. Calculate Factor: Return / Volatility over past n days
        rolling_return = prices / prices.shift(self.n) - 1
        rolling_vol = daily_rets.rolling(self.n).std()
        self.factors = rolling_return / rolling_vol.replace(0, np.nan)

        # 4. Calculate Rolling Correlations
        rolling_corr = daily_rets.rolling(self.k).corr()

        # 5. Generate Signals with Stop-Loss Logic
        start_idx = max(self.n, self.k)
        valid_dates = prices.index[start_idx:]

        prev_selected = []  # Track previously selected assets

        for date in valid_dates:
            if date not in self.factors.index:
                continue

            # 5a. Check stop-loss: if any previously selected asset dropped > threshold
            stopped_assets = set()
            if prev_selected:
                for asset in prev_selected:
                    if asset in daily_rets.columns:
                        daily_ret = daily_rets.loc[date, asset]
                        if daily_ret < -self.stop_loss_pct:
                            stopped_assets.add(asset)

            self.stopped_assets_log[date] = stopped_assets

            # 5b. Get factors, excluding stopped assets
            day_factors = self.factors.loc[date].dropna()
            day_factors = day_factors.drop(stopped_assets, errors='ignore')

            if day_factors.empty:
                prev_selected = []
                continue

            # 5c. Sort by factor descending
            sorted_assets = day_factors.sort_values(ascending=False).index.tolist()

            selected = []

            # Get correlation matrix for this date
            try:
                curr_corr = rolling_corr.loc[date]
            except KeyError:
                prev_selected = []
                continue

            # 5d. Select top M assets with correlation filtering
            for asset in sorted_assets:
                if len(selected) >= self.m:
                    break

                is_correlated = False
                for selected_asset in selected:
                    if asset in curr_corr.index and selected_asset in curr_corr.columns:
                        c = curr_corr.loc[asset, selected_asset]
                        if c > self.corr_threshold:
                            is_correlated = True
                            break

                if not is_correlated:
                    selected.append(asset)

            self.signals[date] = selected
            prev_selected = selected

    def get_target_weights(self, date):
        # Use signal from previous day (T-1 signal -> T open execution)
        if self.dates is None:
             return {}

        try:
            idx = self.dates.get_loc(date)
        except (ValueError, KeyError):
            return {}

        if idx == 0:
            return {}

        prev_date = self.dates[idx - 1]

        if prev_date in self.signals:
            selected = self.signals[prev_date]
            if not selected:
                return {}

            weight = 1.0 / len(selected)
            return {asset: weight for asset in selected}

        return {}


class SectorRotationStrategy(StopLossRotationStrategy):
    """
    行业轮动策略：继承止损轮动策略，使用 A股行业ETF 资产池。
    逻辑与 StopLossRotationStrategy 完全相同，仅限定资产池为 SECTOR_ASSET_CODES。
    """
    def __init__(self, m=3, n=30, k=100, corr_threshold=0.9, stop_loss_pct=0.06):
        super().__init__(m=m, n=n, k=k, corr_threshold=corr_threshold, stop_loss_pct=stop_loss_pct)
        self.sector_assets = set(SECTOR_ASSET_CODES.keys())

    def on_data_loaded(self):
        # 过滤 data_map，只保留 SECTOR_ASSET_CODES 中的资产
        filtered_data_map = {k: v for k, v in self.data_map.items() if k in self.sector_assets}

        # 临时替换 data_map，调用父类方法
        original_data_map = self.data_map
        self.data_map = filtered_data_map

        super().on_data_loaded()

        # 恢复原始 data_map
        self.data_map = original_data_map
