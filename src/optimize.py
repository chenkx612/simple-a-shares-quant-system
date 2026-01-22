import pandas as pd
from .backtest import BacktestEngine
from .strategy import MomentumStrategy
from .config import PORTFOLIOS

def optimize_n():
    n_values = [1, 2, 3, 6, 10, 20, 30, 60, 100]
    engine = BacktestEngine()
    
    results = []
    
    print(f"{'N':<5} | {'Ann. Ret':<10} | {'Sharpe':<8} | {'Max DD':<10} | {'Total Ret':<10}")
    print("-" * 55)
    
    best_sharpe = -100
    best_n = -1
    
    for n in n_values:
        # Suppress warnings for clean output
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Create new engine for each run to ensure clean state
            engine = BacktestEngine()
            strategy = MomentumStrategy(portfolios=PORTFOLIOS, n=n)
            engine.run(strategy)
        
        metrics = engine.get_metrics()
        
        if not metrics:
            continue
            
        print(f"{n:<5} | {metrics['Annualized Return']:<10.2%} | {metrics['Sharpe Ratio']:<8.2f} | {metrics['Max Drawdown']:<10.2%} | {metrics['Total Return']:<10.2%}")
        
        results.append({
            "n": n,
            **metrics
        })
        
        if metrics['Sharpe Ratio'] > best_sharpe:
            best_sharpe = metrics['Sharpe Ratio']
            best_n = n
            
    print("-" * 55)
    print(f"Best N by Sharpe Ratio: {best_n} (Sharpe: {best_sharpe:.2f})")
    return best_n, results

if __name__ == "__main__":
    optimize_n()
