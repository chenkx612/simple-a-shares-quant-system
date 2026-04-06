from itertools import product
from tqdm import tqdm
from .backtest import BacktestEngine
from .strategy import SectorRotationStrategy, FactorThresholdRotationStrategy, EWMAFactorThresholdRotationStrategy
from .config import (
    SECTOR_ASSET_CODES,
    SECTOR_M, SECTOR_N, SECTOR_K, SECTOR_CORR_THRESHOLD, SECTOR_STOP_LOSS_PCT,
    FACTOR_THRESHOLD_M, FACTOR_THRESHOLD_N, FACTOR_THRESHOLD_K,
    FACTOR_THRESHOLD_CORR_THRESHOLD, FACTOR_THRESHOLD_STOP_LOSS_PCT, FACTOR_THRESHOLD_LOWER_BOUND,
    FACTOR_EWMA_M, FACTOR_EWMA_N, FACTOR_EWMA_K,
    FACTOR_EWMA_CORR_THRESHOLD, FACTOR_EWMA_STOP_LOSS_PCT, FACTOR_EWMA_LOWER_BOUND,
)
from .data_loader import load_all_data


class GridSearchOptimizer:
    """通用网格搜索优化器"""

    def __init__(self, strategy_class, param_grid, fixed_params=None,
                 metric='sortino', data_map=None, constraints=None):
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
        if self.metric == 'sortino':
            return metrics.get('Sortino Ratio', -999)
        elif self.metric == 'calmar':
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

        all_combinations = list(self._iter_param_combinations())
        pbar = tqdm(all_combinations, desc="Optimizing", unit="combo") if verbose else all_combinations

        for params in pbar:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                engine = BacktestEngine(data_map=self.data_map)
                strategy = self.strategy_class(**{**self.fixed_params, **params})
                engine.run(strategy)

            metrics = engine.get_metrics()
            score = self._compute_score(metrics)
            satisfies_constraints = self._check_constraints(metrics)

            if verbose and hasattr(pbar, 'set_postfix'):
                pbar.set_postfix({
                    'best_score': f'{best_score:.2f}',
                    'valid': '✓' if satisfies_constraints else ''
                })

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

    def _print_footer(self, best_params, best_score):
        param_names = list(self.param_grid.keys())
        header = " | ".join(f"{p:<6}" for p in param_names)
        print("-" * (len(header) + 12 + (8 if self.constraints else 0)))
        constraint_label = " (constrained)" if self.constraints else ""
        if best_params:
            print(f"\nBest{constraint_label}: {best_params}")
            self._print_best_metrics(best_params)
        else:
            print(f"No valid parameters found{constraint_label}.")

    def _print_best_metrics(self, best_params):
        """展示最优参数组合的详细回测指标"""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            engine = BacktestEngine(data_map=self.data_map)
            strategy = self.strategy_class(**{**self.fixed_params, **best_params})
            engine.run(strategy)

        metrics = engine.get_metrics()
        if not metrics:
            return

        print("\nBacktest Results:")
        for k, v in metrics.items():
            if k.endswith("Ratio"):
                print(f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v:.2%}")


def optimize_sector_params():
    """Grid search optimization for sector rotation strategy parameters.

    约束：|最大回撤| < 年化收益率
    目标：最大化 Sortino 比率
    """
    print(f"\nRunning Sector Rotation Optimization (Sortino, |MaxDD| < AnnRet)...")
    print(f"Asset Pool: {list(SECTOR_ASSET_CODES.keys())}")

    def dd_less_than_return(m):
        return abs(m.get('Max Drawdown', 1)) < m.get('Annualized Return', 0)

    data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
    optimizer = GridSearchOptimizer(
        strategy_class=SectorRotationStrategy,
        param_grid={
            'm': range(3, 11),
            'n': range(10, 51, 5),
        },
        fixed_params={'m': SECTOR_M, 'n': SECTOR_N, 'k': SECTOR_K, 'corr_threshold': SECTOR_CORR_THRESHOLD, 'stop_loss_pct': SECTOR_STOP_LOSS_PCT},
        data_map=data_map,
        constraints=[dd_less_than_return]
    )
    return optimizer.run()


def optimize_factor_threshold_params():
    """Grid search optimization for factor threshold rotation strategy parameters.

    约束：|最大回撤| < 年化收益率
    目标：最大化 Sortino 比率
    """
    print(f"\nRunning Factor Threshold Rotation Optimization (Sortino, |MaxDD| < AnnRet)...")
    print(f"Asset Pool: {list(SECTOR_ASSET_CODES.keys())}")

    def dd_less_than_return(m):
        return abs(m.get('Max Drawdown', 1)) < m.get('Annualized Return', 0)

    data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
    optimizer = GridSearchOptimizer(
        strategy_class=FactorThresholdRotationStrategy,
        param_grid={
            'm': range(4, 7),
            'n': range(15, 40, 5),
            'factor_lower_bound': [i / 10 for i in range(-10, 15, 5)],
            # 'k': [20, 40, 60, 100],
            # 'corr_threshold': [0.7, 0.8, 0.9],
        },
        fixed_params={'m': FACTOR_THRESHOLD_M, 'n': FACTOR_THRESHOLD_N, 'k': FACTOR_THRESHOLD_K, 'corr_threshold': FACTOR_THRESHOLD_CORR_THRESHOLD, 'stop_loss_pct': FACTOR_THRESHOLD_STOP_LOSS_PCT, 'factor_lower_bound': FACTOR_THRESHOLD_LOWER_BOUND},
        data_map=data_map,
        constraints=[dd_less_than_return]
    )
    return optimizer.run()


def optimize_ewma_factor_threshold_params():
    """Grid search optimization for EWMA factor threshold rotation strategy parameters.

    约束：|最大回撤| < 年化收益率
    目标：最大化 Sortino 比率
    """
    print(f"\nRunning EWMA Factor Threshold Rotation Optimization (Sortino, |MaxDD| < AnnRet)...")
    print(f"Asset Pool: {list(SECTOR_ASSET_CODES.keys())}")

    def dd_less_than_return(m):
        return abs(m.get('Max Drawdown', 1)) < m.get('Annualized Return', 0)

    data_map = load_all_data(asset_codes=SECTOR_ASSET_CODES)
    optimizer = GridSearchOptimizer(
        strategy_class=EWMAFactorThresholdRotationStrategy,
        param_grid={
            'm': range(4, 7),
            'n': range(10, 60, 10),
            'factor_lower_bound': [i / 10 for i in range(-10, 15, 5)],
        },
        fixed_params={'m': FACTOR_EWMA_M, 'n': FACTOR_EWMA_N, 'k': FACTOR_EWMA_K, 'corr_threshold': FACTOR_EWMA_CORR_THRESHOLD, 'stop_loss_pct': FACTOR_EWMA_STOP_LOSS_PCT, 'factor_lower_bound': FACTOR_EWMA_LOWER_BOUND},
        data_map=data_map,
        constraints=[dd_less_than_return]
    )
    return optimizer.run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Optimize strategy parameters')
    parser.add_argument('--strategy', type=str, default='ewma_factor_threshold',
                        choices=['sector', 'factor_threshold', 'ewma_factor_threshold'],
                        help='Strategy to optimize')
    args = parser.parse_args()

    if args.strategy == 'sector':
        optimize_sector_params()
    elif args.strategy == 'factor_threshold':
        optimize_factor_threshold_params()
    elif args.strategy == 'ewma_factor_threshold':
        optimize_ewma_factor_threshold_params()
