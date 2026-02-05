from itertools import product
from .backtest import BacktestEngine
from .strategy import StopLossRotationStrategy, SectorRotationStrategy, FactorFloorRotationStrategy
from .config import (
    STOP_LOSS_K, STOP_LOSS_CORR_THRESHOLD,
    SECTOR_ASSET_CODES, SECTOR_K, SECTOR_CORR_THRESHOLD,
    FACTOR_FLOOR_K, FACTOR_FLOOR_CORR_THRESHOLD
)
from .data_loader import load_all_data


class GridSearchOptimizer:
    """通用网格搜索优化器"""

    def __init__(self, strategy_class, param_grid, fixed_params=None,
                 metric='calmar', data_map=None, constraints=None):
        self.strategy_class = strategy_class
        self.param_grid = param_grid
        self.fixed_params = fixed_params or {}
        self.metric = metric
        self.data_map = data_map
        self.constraints = constraints or []

    def _check_constraints(self, metrics):
        """检查所有约束是否满足"""
        if not metrics:
            return False
        return all(c(metrics) for c in self.constraints)

    def _iter_param_combinations(self):
        """生成所有参数组合"""
        keys = list(self.param_grid.keys())
        values = [self.param_grid[k] for k in keys]
        for combo in product(*values):
            yield dict(zip(keys, combo))

    def _compute_score(self, metrics):
        """根据指定指标计算分数"""
        if not metrics:
            return -999
        if self.metric == 'calmar':
            max_dd = abs(metrics.get('Max Drawdown', 0))
            return metrics['Annualized Return'] / max_dd if max_dd > 0.0001 else -999
        elif self.metric == 'sharpe':
            return metrics.get('Sharpe Ratio', -999)
        elif self.metric == 'return':
            return metrics.get('Annualized Return', -999)
        return -999

    def run(self, verbose=True):
        """运行优化，返回 (best_params, all_results)"""
        import warnings

        best_score = -float('inf')
        best_params = None
        results = []

        if verbose:
            self._print_header()

        for params in self._iter_param_combinations():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                engine = BacktestEngine(data_map=self.data_map)
                strategy = self.strategy_class(**params, **self.fixed_params)
                engine.run(strategy)

            metrics = engine.get_metrics()
            score = self._compute_score(metrics)
            satisfies_constraints = self._check_constraints(metrics)

            if verbose:
                self._print_row(params, metrics, score, satisfies_constraints)

            if metrics:
                results.append({
                    "params": params,
                    "score": score,
                    "valid": satisfies_constraints,
                    **metrics
                })

            if satisfies_constraints and score > best_score:
                best_score = score
                best_params = params

        if verbose:
            self._print_footer(best_params, best_score)

        return best_params, results

    def _print_header(self):
        param_names = list(self.param_grid.keys())
        header = " | ".join(f"{p:<6}" for p in param_names)
        valid_col = " | Valid" if self.constraints else ""
        print(f"\n{header} | {'Ann.Ret':<10} | {'Sharpe':<8} | {'MaxDD':<10} | {'Score':<8}{valid_col}")
        print("-" * (70 + (8 if self.constraints else 0)))

    def _print_row(self, params, metrics, score, satisfies_constraints=True):
        if not metrics:
            return
        param_vals = " | ".join(f"{params[p]:<6}" for p in self.param_grid.keys())
        valid_col = f" | {'✓' if satisfies_constraints else '✗':^5}" if self.constraints else ""
        print(f"{param_vals} | {metrics['Annualized Return']:<10.2%} | "
              f"{metrics['Sharpe Ratio']:<8.2f} | {metrics['Max Drawdown']:<10.2%} | {score:<8.2f}{valid_col}")

    def _print_footer(self, best_params, best_score):
        print("-" * (70 + (8 if self.constraints else 0)))
        constraint_label = " (constrained)" if self.constraints else ""
        if best_params:
            print(f"Best{constraint_label}: {best_params} (Score: {best_score:.2f})")
        else:
            print(f"No valid parameters found{constraint_label}.")


def optimize_stop_loss_params():
    """Grid search optimization for stop-loss rotation strategy parameters."""
    print(f"\nRunning Stop-Loss Rotation Optimization...")
    print(f"Fixed Parameters: K={STOP_LOSS_K}, Corr Threshold={STOP_LOSS_CORR_THRESHOLD}")

    optimizer = GridSearchOptimizer(
        strategy_class=StopLossRotationStrategy,
        param_grid={
            'm': [3, 4, 5, 10],
            'n': [10, 20, 30, 60],
            'stop_loss_pct': [0.05, 0.06, 0.07, 0.10]
        },
        fixed_params={'k': STOP_LOSS_K, 'corr_threshold': STOP_LOSS_CORR_THRESHOLD}
    )
    return optimizer.run()


def optimize_sector_params():
    """Grid search optimization for sector rotation strategy parameters.

    约束：|最大回撤| < 年化收益率
    目标：最大化夏普率
    """
    print(f"\nRunning Sector Rotation Optimization (Sharpe, |MaxDD| < AnnRet)...")
    print(f"Fixed Parameters: K={SECTOR_K}, Corr Threshold={SECTOR_CORR_THRESHOLD}")
    print(f"Asset Pool: {list(SECTOR_ASSET_CODES.keys())}")

    def dd_less_than_return(m):
        return abs(m.get('Max Drawdown', 1)) < m.get('Annualized Return', 0)

    data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
    optimizer = GridSearchOptimizer(
        strategy_class=SectorRotationStrategy,
        param_grid={
            'm': [3, 4, 5, 10],
            'n': [10, 20, 30, 60],
            'stop_loss_pct': [0.05, 0.06, 0.07, 0.10]
        },
        fixed_params={'k': SECTOR_K, 'corr_threshold': SECTOR_CORR_THRESHOLD},
        data_map=data_map,
        metric='sharpe',
        constraints=[dd_less_than_return]
    )
    return optimizer.run()

def optimize_factor_floor_params():
    """Grid search optimization for factor floor rotation strategy parameters.

    约束：|最大回撤| < 年化收益率
    目标：最大化夏普率
    """
    print(f"\nRunning Factor Floor Rotation Optimization (Sharpe, |MaxDD| < AnnRet)...")
    print(f"Fixed Parameters: K={FACTOR_FLOOR_K}, Corr Threshold={FACTOR_FLOOR_CORR_THRESHOLD}")
    print(f"Asset Pool: {list(SECTOR_ASSET_CODES.keys())}")

    def dd_less_than_return(m):
        return abs(m.get('Max Drawdown', 1)) < m.get('Annualized Return', 0)

    data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
    optimizer = GridSearchOptimizer(
        strategy_class=FactorFloorRotationStrategy,
        param_grid={
            'm': [3, 4, 5],
            'n': [10, 20, 30],
            'stop_loss_pct': [0.05, 0.06, 0.07],
            'factor_floor': [0.0, 0.1, 0.2, 0.3]
        },
        fixed_params={'k': FACTOR_FLOOR_K, 'corr_threshold': FACTOR_FLOOR_CORR_THRESHOLD},
        data_map=data_map,
        metric='sharpe',
        constraints=[dd_less_than_return]
    )
    return optimizer.run()


if __name__ == "__main__":
    optimize_stop_loss_params()
