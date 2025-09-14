"""
Generate Final Portfolio Comparison with New Sortino Optimizer

Creates a comprehensive CSV comparing:
1. Single-asset strategies
2. Old complex optimizer results  
3. New simplified Sortino optimizer results
"""

import pandas as pd
import numpy as np
from portfolio.ils_data_manager import ILSDataManager
from portfolio.sortino_optimizer import SortinoOptimizer
import warnings
warnings.filterwarnings('ignore')

def generate_final_comparison():
    """Generate comprehensive comparison of all strategies"""
    
    print("="*80)
    print(" GENERATING FINAL PORTFOLIO COMPARISON")
    print("="*80)
    
    # Load data
    print("\nLoading data...")
    data_manager = ILSDataManager()
    optimizer = SortinoOptimizer(data_manager)
    
    results = []
    
    # 1. Single Asset Strategies
    print("\nCalculating single-asset strategies...")
    single_assets = [
        'NASDAQ_Total_Return',
        'US_Large_Cap_SP500', 
        'Gold_Futures',
        'Israel_TA125',
        'India_NIFTY',
        'Germany_DAX',
        'US_REIT_Select'
    ]
    
    for asset_name in single_assets:
        if asset_name in data_manager.returns_data.columns:
            returns = data_manager.returns_data[asset_name]
            annual_return = returns.mean() * 12
            annual_vol = returns.std() * np.sqrt(12)
            rf = data_manager.risk_free_rate.mean()
            sharpe = (annual_return - rf) / annual_vol
            
            # Calculate Sortino
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_dev = downside_returns.std() * np.sqrt(12)
            else:
                downside_dev = 0.001
            sortino = (annual_return - rf) / downside_dev
            
            # Max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_dd = abs(drawdown.min())
            
            row = {
                'Strategy_Type': 'Single Asset',
                'Strategy_Name': asset_name.replace('_', ' '),
                'Aggressiveness': 'N/A',
                'Expected_Return_%': annual_return * 100,
                'Volatility_%': annual_vol * 100,
                'Sharpe_Ratio': sharpe,
                'Sortino_Ratio': sortino,
                'Max_Drawdown_%': max_dd * 100,
                f'{asset_name}_%': 100.0
            }
            
            # Add zeros for other assets
            for other_asset in single_assets:
                if other_asset != asset_name:
                    row[f'{other_asset}_%'] = 0.0
                    
            results.append(row)
    
    # 2. New Sortino Optimizer Results
    print("\nOptimizing with new Sortino optimizer...")
    optimization_profiles = [
        (0.0, "Ultra Conservative (New)"),
        (0.25, "Conservative (New)"),
        (0.5, "Moderate (New)"),
        (0.75, "Aggressive (New)"),
        (0.95, "Very Aggressive (New)"),
        (1.0, "Ultra Aggressive (New)")
    ]
    
    for aggressiveness, label in optimization_profiles:
        print(f"  Optimizing {label}...")
        result = optimizer.optimize(aggressiveness)
        
        row = {
            'Strategy_Type': 'Sortino Optimized',
            'Strategy_Name': label,
            'Aggressiveness': aggressiveness,
            'Expected_Return_%': result['expected_return'] * 100,
            'Volatility_%': result['volatility'] * 100,
            'Sharpe_Ratio': result['sharpe_ratio'],
            'Sortino_Ratio': result['sortino_ratio'],
            'Max_Drawdown_%': result['max_drawdown'] * 100
        }
        
        # Add individual asset weights
        for asset in data_manager.returns_data.columns:
            row[f'{asset}_%'] = result['weights'].get(asset, 0.0) * 100
            
        results.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Reorder columns
    base_cols = ['Strategy_Type', 'Strategy_Name', 'Aggressiveness', 
                 'Expected_Return_%', 'Volatility_%', 'Sharpe_Ratio', 
                 'Sortino_Ratio', 'Max_Drawdown_%']
    asset_cols = [col for col in df.columns if col.endswith('_%') and col not in base_cols]
    df = df[base_cols + asset_cols]
    
    # Sort by expected return
    df = df.sort_values('Expected_Return_%', ascending=False)
    
    # Save to CSV
    output_file = 'final_portfolio_comparison.csv'
    df.to_csv(output_file, index=False, float_format='%.2f')
    print(f"\nResults saved to: {output_file}")
    
    # Print summary
    print("\n" + "="*80)
    print(" SUMMARY OF KEY RESULTS")
    print("="*80)
    
    # Best performers
    print("\nTop 5 Strategies by Return:")
    for i, row in df.head(5).iterrows():
        print(f"  {row['Strategy_Name']:<30} {row['Expected_Return_%']:>6.1f}% return, {row['Volatility_%']:>5.1f}% vol, {row['Sharpe_Ratio']:>5.2f} Sharpe")
    
    # Check new optimizer performance
    new_aggressive = df[df['Strategy_Name'] == 'Aggressive (New)'].iloc[0]
    new_ultra = df[df['Strategy_Name'] == 'Ultra Aggressive (New)'].iloc[0]
    sp500 = df[df['Strategy_Name'] == 'US Large Cap SP500'].iloc[0]
    nasdaq = df[df['Strategy_Name'] == 'NASDAQ Total Return'].iloc[0]
    
    print("\n" + "="*80)
    print(" OPTIMIZATION SUCCESS VERIFICATION")
    print("="*80)
    
    print(f"\nAggressive (New) vs S&P 500:")
    print(f"  Aggressive: {new_aggressive['Expected_Return_%']:.1f}% return, {new_aggressive['Sharpe_Ratio']:.2f} Sharpe")
    print(f"  S&P 500:    {sp500['Expected_Return_%']:.1f}% return, {sp500['Sharpe_Ratio']:.2f} Sharpe")
    print(f"  => Aggressive {'BEATS' if new_aggressive['Expected_Return_%'] > sp500['Expected_Return_%'] else 'LOSES TO'} S&P 500 by {abs(new_aggressive['Expected_Return_%'] - sp500['Expected_Return_%']):.1f}%")
    
    print(f"\nUltra Aggressive (New) vs NASDAQ:")
    print(f"  Ultra Aggressive: {new_ultra['Expected_Return_%']:.1f}% return, {new_ultra['Sharpe_Ratio']:.2f} Sharpe")
    print(f"  NASDAQ:          {nasdaq['Expected_Return_%']:.1f}% return, {nasdaq['Sharpe_Ratio']:.2f} Sharpe")
    print(f"  => Ultra Aggressive {'MATCHES' if abs(new_ultra['Expected_Return_%'] - nasdaq['Expected_Return_%']) < 0.5 else 'DIFFERS FROM'} NASDAQ")
    
    if new_aggressive['Expected_Return_%'] > sp500['Expected_Return_%'] * 0.9 and \
       new_ultra['Expected_Return_%'] > nasdaq['Expected_Return_%'] * 0.95:
        print("\n" + "="*60)
        print(" SUCCESS! NEW OPTIMIZER ACHIEVES COMPETITIVE RETURNS")
        print("="*60)
    
    return df

if __name__ == "__main__":
    generate_final_comparison()