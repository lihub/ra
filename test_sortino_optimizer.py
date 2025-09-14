"""
Test the Simplified Sortino Optimizer

Verifies that the new optimizer:
1. Works correctly for different aggressiveness levels
2. Produces sensible allocations
3. Achieves good returns for aggressive investors
"""

import numpy as np
import pandas as pd
from portfolio.ils_data_manager import ILSDataManager
from portfolio.sortino_optimizer import SortinoOptimizer
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

def test_sortino_optimizer():
    """Test the Sortino optimizer with various aggressiveness levels"""
    
    print("="*80)
    print(" TESTING SIMPLIFIED SORTINO OPTIMIZER")
    print("="*80)
    
    # Load data
    print("\nLoading data...")
    data_manager = ILSDataManager()
    optimizer = SortinoOptimizer(data_manager)
    
    # Test different aggressiveness levels
    test_levels = [
        (0.0, "Ultra Conservative"),
        (0.25, "Conservative"),
        (0.5, "Moderate"),
        (0.75, "Aggressive"),
        (1.0, "Ultra Aggressive")
    ]
    
    results = []
    
    for aggressiveness, label in test_levels:
        print(f"\n{'='*60}")
        print(f" {label} (Aggressiveness: {aggressiveness:.2f})")
        print("="*60)
        
        # Run optimization
        result = optimizer.optimize(aggressiveness)
        
        print(f"\nOptimization Success: {result['optimization_success']}")
        print(f"Expected Return: {result['expected_return']*100:.1f}%")
        print(f"Volatility: {result['volatility']*100:.1f}%")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio: {result['sortino_ratio']:.2f}")
        print(f"Max Drawdown: {result['max_drawdown']*100:.1f}%")
        
        # Show top allocations
        print("\nTop Allocations:")
        sorted_weights = sorted(result['weights'].items(), key=lambda x: x[1], reverse=True)
        for asset, weight in sorted_weights[:5]:
            if weight > 0.01:
                print(f"  {asset:<30} {weight*100:>6.1f}%")
        
        # Store for comparison
        results.append({
            'Strategy': label,
            'Aggressiveness': aggressiveness,
            'Return': result['expected_return'],
            'Volatility': result['volatility'],
            'Sharpe': result['sharpe_ratio'],
            'Sortino': result['sortino_ratio'],
            'Max_DD': result['max_drawdown'],
            'Top_Asset': sorted_weights[0][0] if sorted_weights else 'None',
            'Top_Weight': sorted_weights[0][1] if sorted_weights else 0
        })
    
    # Compare with benchmarks
    print("\n" + "="*80)
    print(" BENCHMARK COMPARISON")
    print("="*80)
    
    # Calculate S&P 500 and NASDAQ performance
    sp500_returns = data_manager.returns_data['US_Large_Cap_SP500']
    nasdaq_returns = data_manager.returns_data['NASDAQ_Total_Return']
    rf = data_manager.risk_free_rate.mean()
    
    # S&P 500 metrics
    sp500_annual_return = sp500_returns.mean() * 12
    sp500_annual_vol = sp500_returns.std() * np.sqrt(12)
    sp500_sharpe = (sp500_annual_return - rf) / sp500_annual_vol
    sp500_downside = sp500_returns[sp500_returns < 0].std() * np.sqrt(12) if len(sp500_returns[sp500_returns < 0]) > 0 else 0.001
    sp500_sortino = (sp500_annual_return - rf) / sp500_downside
    
    # NASDAQ metrics  
    nasdaq_annual_return = nasdaq_returns.mean() * 12
    nasdaq_annual_vol = nasdaq_returns.std() * np.sqrt(12)
    nasdaq_sharpe = (nasdaq_annual_return - rf) / nasdaq_annual_vol
    nasdaq_downside = nasdaq_returns[nasdaq_returns < 0].std() * np.sqrt(12) if len(nasdaq_returns[nasdaq_returns < 0]) > 0 else 0.001
    nasdaq_sortino = (nasdaq_annual_return - rf) / nasdaq_downside
    
    # Add benchmarks to results
    results.append({
        'Strategy': 'S&P 500 (Benchmark)',
        'Aggressiveness': '-',
        'Return': sp500_annual_return,
        'Volatility': sp500_annual_vol,
        'Sharpe': sp500_sharpe,
        'Sortino': sp500_sortino,
        'Max_DD': 0.175,  # Approximate
        'Top_Asset': 'US_Large_Cap_SP500',
        'Top_Weight': 1.0
    })
    
    results.append({
        'Strategy': 'NASDAQ (Benchmark)',
        'Aggressiveness': '-',
        'Return': nasdaq_annual_return,
        'Volatility': nasdaq_annual_vol,
        'Sharpe': nasdaq_sharpe,
        'Sortino': nasdaq_sortino,
        'Max_DD': 0.241,  # Approximate
        'Top_Asset': 'NASDAQ_Total_Return',
        'Top_Weight': 1.0
    })
    
    # Create comparison table
    df = pd.DataFrame(results)
    
    # Format for display
    df['Return'] = df['Return'].apply(lambda x: f"{x*100:.1f}%" if isinstance(x, float) else x)
    df['Volatility'] = df['Volatility'].apply(lambda x: f"{x*100:.1f}%" if isinstance(x, float) else x)
    df['Sharpe'] = df['Sharpe'].apply(lambda x: f"{x:.2f}" if isinstance(x, float) else x)
    df['Sortino'] = df['Sortino'].apply(lambda x: f"{x:.2f}" if isinstance(x, float) else x)
    df['Max_DD'] = df['Max_DD'].apply(lambda x: f"{x*100:.1f}%" if isinstance(x, float) else x)
    df['Top_Weight'] = df['Top_Weight'].apply(lambda x: f"{x*100:.1f}%" if isinstance(x, float) else x)
    
    print("\nFull Comparison Table:")
    print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    
    # Key insights
    print("\n" + "="*80)
    print(" KEY INSIGHTS")
    print("="*80)
    
    # Check if aggressive portfolios compete with benchmarks
    aggressive_return = results[3]['Return']  # Index 3 is Aggressive
    ultra_aggressive_return = results[4]['Return']  # Index 4 is Ultra Aggressive
    
    print(f"\n1. Aggressive Portfolio Return: {aggressive_return*100:.1f}%")
    print(f"   S&P 500 Return: {sp500_annual_return*100:.1f}%")
    print(f"   Difference: {(aggressive_return - sp500_annual_return)*100:.1f}%")
    
    print(f"\n2. Ultra Aggressive Portfolio Return: {ultra_aggressive_return*100:.1f}%")
    print(f"   NASDAQ Return: {nasdaq_annual_return*100:.1f}%")  
    print(f"   Difference: {(ultra_aggressive_return - nasdaq_annual_return)*100:.1f}%")
    
    if aggressive_return > sp500_annual_return * 0.8:
        print("\n✓ SUCCESS: Aggressive portfolios achieve competitive returns!")
    else:
        print("\n✗ ISSUE: Aggressive portfolios still underperforming significantly")
        print("  Need to adjust weight limits or constraints")
    
    return df

if __name__ == "__main__":
    test_sortino_optimizer()