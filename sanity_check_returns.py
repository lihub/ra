"""
Sanity Check - Individual Asset Performance

Check the performance of holding 100% in each individual asset
to validate the portfolio optimization results.
"""

import logging
import warnings
from tabulate import tabulate
from portfolio.ils_data_manager import ILSDataManager

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)

def main():
    """Show individual asset performance"""
    
    print("\n" + "="*80)
    print(" SANITY CHECK: INDIVIDUAL ASSET PERFORMANCE (ILS TERMS)")
    print("="*80)
    
    # Load data manager
    dm = ILSDataManager()
    
    print(f"\nData Overview:")
    print(f"  Assets loaded: {len(dm.returns_data.columns)}")
    print(f"  Data period: {dm.returns_data.index[0]} to {dm.returns_data.index[-1]}")
    print(f"  Number of months: {len(dm.returns_data)}")
    print(f"  Risk-free rate: {dm.avg_risk_free_rate:.2%} annually")
    
    # Get individual asset statistics
    stats = dm.summary_statistics()
    
    # Prepare table data
    table_data = []
    for asset_name, asset_stats in stats.items():
        table_data.append([
            asset_name.replace('_', ' '),
            f"{asset_stats['annual_return']:.1%}",
            f"{asset_stats['annual_volatility']:.1%}",
            f"{asset_stats['sharpe_ratio']:.2f}",
            asset_stats.get('category', 'unknown'),
            asset_stats.get('region', 'unknown')
        ])
    
    # Sort by annual return
    table_data.sort(key=lambda x: float(x[1].replace('%', '')), reverse=True)
    
    print(f"\nIndividual Asset Performance (Sorted by Return):")
    print(tabulate(table_data,
                  headers=['Asset', 'Annual Return', 'Volatility', 'Sharpe', 'Category', 'Region'],
                  tablefmt='grid'))
    
    # Show summary statistics
    returns = [float(row[1].replace('%', '')) for row in table_data]
    volatilities = [float(row[2].replace('%', '')) for row in table_data]
    sharpes = [float(row[3]) for row in table_data]
    
    print(f"\nSummary Statistics:")
    print(f"  Best performing asset: {max(returns):.1f}% return")
    print(f"  Worst performing asset: {min(returns):.1f}% return")
    print(f"  Average return: {sum(returns)/len(returns):.1f}%")
    print(f"  Number of positive return assets: {sum(1 for r in returns if r > 0)}/{len(returns)}")
    print(f"  Risk-free rate: {dm.avg_risk_free_rate:.1%}")
    
    # Check if there's a data issue
    if max(returns) < 2.0:  # If best asset is less than 2%
        print(f"\n⚠️  WARNING: ALL ASSETS HAVE VERY LOW RETURNS!")
        print(f"   This suggests there might be a data processing issue.")
        print(f"   Let's investigate the raw data...")
        
        # Show some raw return statistics
        print(f"\nRaw Monthly Returns Analysis:")
        monthly_stats = []
        for col in dm.returns_data.columns[:5]:  # First 5 assets
            monthly_returns = dm.returns_data[col]
            annual_equiv = (1 + monthly_returns.mean())**12 - 1
            monthly_stats.append([
                col.replace('_', ' '),
                f"{monthly_returns.mean():.3f}",
                f"{annual_equiv:.1%}",
                f"{monthly_returns.min():.3f}",
                f"{monthly_returns.max():.3f}",
                f"{monthly_returns.std():.3f}"
            ])
        
        print(tabulate(monthly_stats,
                      headers=['Asset', 'Avg Monthly', 'Annualized', 'Min Monthly', 'Max Monthly', 'Monthly Vol'],
                      tablefmt='simple'))
        
        # Check data range
        print(f"\nData Range Check:")
        print(f"  First month return range: {dm.returns_data.iloc[0].min():.3f} to {dm.returns_data.iloc[0].max():.3f}")
        print(f"  Last month return range: {dm.returns_data.iloc[-1].min():.3f} to {dm.returns_data.iloc[-1].max():.3f}")
        
        # Check for extreme values
        all_returns = dm.returns_data.values.flatten()
        print(f"  Overall return range: {all_returns.min():.3f} to {all_returns.max():.3f}")
        print(f"  Percentage of negative returns: {(all_returns < 0).sum() / len(all_returns) * 100:.1f}%")
        
    # Compare to risk-free rate
    risk_free_annual = dm.avg_risk_free_rate
    assets_beating_rf = sum(1 for r in returns if r/100 > risk_free_annual)
    
    print(f"\nRisk-Free Rate Comparison:")
    print(f"  Assets beating risk-free rate: {assets_beating_rf}/{len(returns)}")
    print(f"  Risk-free rate: {risk_free_annual:.1%}")
    
    if assets_beating_rf == 0:
        print(f"  ⚠️  NO ASSETS BEAT THE RISK-FREE RATE!")
        print(f"     This is highly unusual and suggests a data issue.")
        
        # Check risk-free rate calculation
        print(f"\nRisk-Free Rate Deep Dive:")
        print(f"  Raw risk-free rate mean: {dm.risk_free_rate.mean():.4f}")
        print(f"  Risk-free rate range: {dm.risk_free_rate.min():.4f} to {dm.risk_free_rate.max():.4f}")
        print(f"  First few risk-free rates: {list(dm.risk_free_rate.head())}")
        
    # Show best and worst performers
    print(f"\nBest Performers:")
    for i in range(min(3, len(table_data))):
        print(f"  {i+1}. {table_data[i][0]}: {table_data[i][1]} return, {table_data[i][2]} volatility")
        
    print(f"\nWorst Performers:")
    for i in range(min(3, len(table_data))):
        idx = len(table_data) - 1 - i
        print(f"  {i+1}. {table_data[idx][0]}: {table_data[idx][1]} return, {table_data[idx][2]} volatility")

if __name__ == "__main__":
    main()