import pandas as pd
import numpy as np
from .config import START_DATE, COMMISSION_RATE, DATA_DIR
from .data_loader import load_all_data
from .strategy import Strategy

class BacktestEngine:
    def __init__(self, initial_capital=100000.0, commission_rate=COMMISSION_RATE, start_date=START_DATE, data_map=None):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.start_date = pd.Timestamp(start_date)

        # 支持传入自定义 data_map，或使用默认资产池
        self.data_map = data_map if data_map is not None else load_all_data()
        self.aligned_open = None
        self.aligned_close = None
        self.available_assets = []

        self._prepare_data()

        # Account State
        self.cash = initial_capital
        self.positions = {} # {asset_code: shares}
        self.history = [] # List of dicts recording daily state

        # PnL tracking
        self.asset_pnl = {}  # {asset: 累计已实现盈亏}
        self.asset_cost_basis = {}  # {asset: 平均成本价}

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

        # 回测结束，计算未平仓资产的浮盈/浮亏
        if self.history:
            final_prices = self.aligned_close.iloc[-1]
            for asset, shares in self.positions.items():
                if shares > 0:
                    price = final_prices.get(asset, 0)
                    cost_basis = self.asset_cost_basis.get(asset, 0)
                    unrealized_pnl = (price - cost_basis) * shares
                    self.asset_pnl[asset] = self.asset_pnl.get(asset, 0) + unrealized_pnl

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
                        commission = value * self.commission_rate
                        # 计算已实现盈亏
                        cost_basis = self.asset_cost_basis.get(asset, 0)
                        realized_pnl = (price - cost_basis) * shares - commission
                        self.asset_pnl[asset] = self.asset_pnl.get(asset, 0) + realized_pnl
                        # 更新账户
                        self.cash += value - commission
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
            commission = abs(trade_val) * self.commission_rate

            # 更新盈亏和成本基础
            if diff_shares > 0:
                # 买入：更新平均成本
                old_cost = self.asset_cost_basis.get(asset, 0)
                old_shares = current_shares
                new_cost = (old_cost * old_shares + price * diff_shares) / (old_shares + diff_shares) if (old_shares + diff_shares) > 0 else 0
                self.asset_cost_basis[asset] = new_cost
                # 买入手续费计入已实现亏损
                self.asset_pnl[asset] = self.asset_pnl.get(asset, 0) - commission
            else:
                # 卖出：计算已实现盈亏
                cost_basis = self.asset_cost_basis.get(asset, 0)
                realized_pnl = (price - cost_basis) * (-diff_shares) - commission
                self.asset_pnl[asset] = self.asset_pnl.get(asset, 0) + realized_pnl

            # Update
            self.cash -= (trade_val + commission)
            self.positions[asset] = current_shares + diff_shares

        # Handle assets that are not in target_weights (Sell them)
        for asset in list(self.positions.keys()):
            if asset not in target_weights and self.positions[asset] > 0:
                price = current_prices.get(asset, 0)
                if price > 0:
                    shares = self.positions[asset]
                    value = shares * price
                    commission = value * self.commission_rate
                    # 计算已实现盈亏
                    cost_basis = self.asset_cost_basis.get(asset, 0)
                    realized_pnl = (price - cost_basis) * shares - commission
                    self.asset_pnl[asset] = self.asset_pnl.get(asset, 0) + realized_pnl
                    # 更新账户
                    self.cash += value - commission
                    self.positions[asset] = 0

    def _calculate_total_value(self, prices):
        val = self.cash
        for asset, shares in self.positions.items():
            if shares != 0:
                price = prices.get(asset, 0)
                if not pd.isna(price):
                    val += shares * price
        return val

    def get_asset_pnl(self) -> pd.DataFrame:
        """返回每个资产的盈亏统计"""
        records = []
        for asset, pnl in self.asset_pnl.items():
            records.append({
                'asset': asset,
                'total_pnl': pnl,
                'contribution': pnl / self.initial_capital
            })
        if not records:
            return pd.DataFrame(columns=['asset', 'total_pnl', 'contribution'])
        return pd.DataFrame(records).sort_values('total_pnl', ascending=False)

    def get_metrics(self):
        if not self.history:
            return {}
            
        df = pd.DataFrame(self.history).set_index('date')
        df['returns'] = df['total_value'].pct_change().fillna(0)
        
        total_ret = (df['total_value'].iloc[-1] / self.initial_capital) - 1
        days = len(df)
        ann_ret = (1 + total_ret) ** (252/days) - 1
        
        rf = 0.01

        # Sortino Ratio (只考虑下行波动率)
        negative_returns = df['returns'][df['returns'] < 0]
        downside_vol = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino = (ann_ret - rf) / downside_vol if downside_vol != 0 else 0

        # Max Drawdown
        wealth = df['total_value']
        peak = wealth.cummax()
        drawdown = (wealth - peak) / peak
        max_dd = drawdown.min()

        # Calmar Ratio (年化收益 / |最大回撤|)
        calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0

        return {
            "Annualized Return": ann_ret,
            "Max Drawdown": max_dd,
            "Sortino Ratio": sortino,
            "Calmar Ratio": calmar,
        }

if __name__ == "__main__":
    from .strategy import SmartRotationStrategy
    from .config import SMART_M, SMART_N, SMART_K, CORR_THRESHOLD

    engine = BacktestEngine()
    strategy = SmartRotationStrategy(m=SMART_M, n=SMART_N, k=SMART_K, corr_threshold=CORR_THRESHOLD)

    result = engine.run(strategy)
    metrics = engine.get_metrics()

    print("\nBacktest Results:")
    for k, v in metrics.items():
        print(f"{k}: {v:.2%}" if not k.endswith("Ratio") else f"{k}: {v:.2f}")

    print("\nAsset PnL Contribution:")
    asset_pnl = engine.get_asset_pnl()
    if not asset_pnl.empty:
        for _, row in asset_pnl.iterrows():
            print(f"  {row['asset']}: {row['total_pnl']:+,.2f} ({row['contribution']:+.2%})")
        print(f"  Total contribution: {asset_pnl['contribution'].sum():.2%}")
