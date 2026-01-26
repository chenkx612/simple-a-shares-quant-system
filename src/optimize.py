import pandas as pd
from .backtest import BacktestEngine
from .strategy import MomentumStrategy, SmartRotationStrategy
from .config import PORTFOLIOS, SMART_K, CORR_THRESHOLD

def optimize_n():
    n_values = [1, 2, 3, 6, 10, 20, 30, 60, 100]
    engine = BacktestEngine()
    
    results = []
    
    print(f"{'N':<5} | {'Ann. Ret':<10} | {'Sharpe':<8} | {'Max DD':<10} | {'Calmar':<8} | {'Total Ret':<10}")
    print("-" * 65)
    
    best_calmar = -100
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
            
        max_dd = abs(metrics['Max Drawdown'])
        calmar = metrics['Annualized Return'] / max_dd if max_dd > 0.0001 else -999
            
        print(f"{n:<5} | {metrics['Annualized Return']:<10.2%} | {metrics['Sharpe Ratio']:<8.2f} | {metrics['Max Drawdown']:<10.2%} | {calmar:<8.2f} | {metrics['Total Return']:<10.2%}")
        
        results.append({
            "n": n,
            "Calmar Ratio": calmar,
            **metrics
        })
        
        if calmar > best_calmar:
            best_calmar = calmar
            best_n = n
            
    print("-" * 65)
    print(f"Best N by Calmar Ratio: {best_n} (Calmar: {best_calmar:.2f})")
    return best_n, results

def optimize_smart_params():
    # Optimization ranges
    m_values = [3, 4, 5, 6, 10]
    n_values = [10, 20, 30, 60, 100]
    
    print(f"\nRunning Smart Rotation Optimization...")
    print(f"Fixed Parameters: K={SMART_K}, Corr Threshold={CORR_THRESHOLD}")
    print(f"{'M':<3} | {'N':<5} | {'Ann. Ret':<10} | {'Sharpe':<8} | {'Max DD':<10} | {'Calmar':<8} | {'Total Ret':<10}")
    print("-" * 70)
    
    best_calmar = -100
    best_params = (2, 20) # Default fallback
    results = []
    
    import warnings
    
    for m in m_values:
        for n in n_values:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                engine = BacktestEngine()
                strategy = SmartRotationStrategy(m=m, n=n, k=SMART_K, corr_threshold=CORR_THRESHOLD)
                engine.run(strategy)
                
            metrics = engine.get_metrics()
            
            if not metrics:
                continue
                
            max_dd = abs(metrics['Max Drawdown'])
            calmar = metrics['Annualized Return'] / max_dd if max_dd > 0.0001 else -999
            
            print(f"{m:<3} | {n:<5} | {metrics['Annualized Return']:<10.2%} | {metrics['Sharpe Ratio']:<8.2f} | {metrics['Max Drawdown']:<10.2%} | {calmar:<8.2f} | {metrics['Total Return']:<10.2%}")
            
            results.append({
                "m": m,
                "n": n,
                "Calmar Ratio": calmar,
                **metrics
            })
            
            if calmar > best_calmar:
                best_calmar = calmar
                best_params = (m, n)
    
    print("-" * 70)
    print(f"Best Parameters: M={best_params[0]}, N={best_params[1]} (Calmar: {best_calmar:.2f})")
    return best_params, results

if __name__ == "__main__":
    optimize_n()

