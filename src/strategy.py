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

    @property
    @abstractmethod
    def asset_codes(self) -> dict:
        """Return the asset codes mapping for this strategy."""
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

class SectorRotationStrategy(Strategy):
    """
    行业轮动策略：使用 A股行业ETF 资产池，基于风险调整动量因子选股，
    加相关性过滤和止损机制。
    """
    def __init__(self, m=3, n=30, k=100, corr_threshold=0.9, stop_loss_pct=0.06):
        super().__init__()
        self.m = m
        self.n = n
        self.k = k
        self.corr_threshold = corr_threshold
        self.stop_loss_pct = stop_loss_pct
        self.signals = {}  # Date -> [selected_assets]
        self.stopped_assets_log = {}  # Date -> set of stopped assets (for debugging)
        self.sector_assets = set(SECTOR_ASSET_CODES.keys())

    @property
    def asset_codes(self):
        return SECTOR_ASSET_CODES

    def _compute_factors(self, prices, daily_rets):
        """计算轮动因子：Return / Volatility（简化Sharpe）。子类可重写此方法。"""
        rolling_return = prices / prices.shift(self.n) - 1
        rolling_vol = daily_rets.rolling(self.n).std()
        return rolling_return / rolling_vol.replace(0, np.nan)

    def _filter_factors(self, day_factors):
        """过滤因子：子类可重写此方法实现因子下限等过滤逻辑。"""
        return day_factors

    def on_data_loaded(self):
        # 过滤 data_map，只保留 SECTOR_ASSET_CODES 中的资产
        filtered_data_map = {k: v for k, v in self.data_map.items() if k in self.sector_assets}

        # 1. Align Close Prices
        dfs = []
        for asset_key, df in filtered_data_map.items():
            if 'close' in df.columns:
                s = df['close'].rename(asset_key)
                dfs.append(s)

        if not dfs:
            return

        prices = pd.concat(dfs, axis=1).sort_index().ffill()

        # 2. Calculate Daily Returns
        daily_rets = prices.pct_change().fillna(0)

        # 3. Calculate Factor
        self.factors = self._compute_factors(prices, daily_rets)

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
            day_factors = self._filter_factors(day_factors)

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


class SortinoRotationStrategy(SectorRotationStrategy):
    """
    行业轮动策略（Sortino因子）：使用 Return / Downside Volatility 作为轮动因子，
    只惩罚下行波动，不惩罚上行波动。
    """

    def _compute_factors(self, prices, daily_rets):
        rolling_return = prices / prices.shift(self.n) - 1
        downside_rets = daily_rets.clip(upper=0)
        rolling_downside_vol = downside_rets.rolling(self.n).std()
        return rolling_return / rolling_downside_vol.replace(0, np.nan)


class FactorThresholdRotationStrategy(SectorRotationStrategy):
    """
    行业轮动策略（因子下限）：在板块轮动基础上增加因子下限过滤。
    只有因子值 > factor_lower_bound 的资产才会被考虑买入，否则空仓。
    每只资产仓位固定为 1/m，不足 m 只时剩余仓位空仓。
    """

    def __init__(self, factor_lower_bound=0.0, **kwargs):
        super().__init__(**kwargs)
        self.factor_lower_bound = factor_lower_bound

    def _filter_factors(self, day_factors):
        return day_factors[day_factors > self.factor_lower_bound]

    def get_target_weights(self, date):
        weights = super().get_target_weights(date)
        if not weights:
            return weights
        # 固定每只资产仓位为 1/m，不随实际持仓数量变化
        fixed_weight = 1.0 / self.m
        return {asset: fixed_weight for asset in weights}
