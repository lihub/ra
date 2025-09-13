"""
Analyze Currency Impact on Indian Assets

Shows the cumulative performance of Indian equities in INR terms vs ILS terms
and the INR/ILS exchange rate to understand the currency conversion impact.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def load_and_process_data():
    """Load raw price data and FX rates"""
    
    data_path = Path("processed_data")
    
    # Load Indian equity data (prices)
    indian_assets = [
        'clean_India_NIFTY.csv'
    ]
    
    # Load INR/ILS FX rate
    fx_file = 'clean_INR_ILS_FX.csv'
    
    # Load data
    equity_data = {}
    for asset_file in indian_assets:
        asset_name = asset_file.replace('clean_', '').replace('.csv', '')
        df = pd.read_csv(data_path / asset_file)
        df.columns = ['date', 'price']
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        equity_data[asset_name] = df['price']
    
    # Load FX rate
    fx_df = pd.read_csv(data_path / fx_file)
    fx_df.columns = ['date', 'fx_rate']
    fx_df['date'] = pd.to_datetime(fx_df['date'])
    fx_df = fx_df.set_index('date').sort_index()
    
    return equity_data, fx_df['fx_rate']

def calculate_cumulative_returns(price_series):
    """Calculate cumulative returns normalized to start at 1"""
    return price_series / price_series.iloc[0]

def main():
    """Create comprehensive currency impact analysis for Indian assets"""
    
    print("Loading Indian data...")
    equity_data, fx_rate = load_and_process_data()
    
    # Align all data to common dates
    common_dates = None
    for asset_name, prices in equity_data.items():
        if common_dates is None:
            common_dates = prices.index
        else:
            common_dates = common_dates.intersection(prices.index)
    
    common_dates = common_dates.intersection(fx_rate.index)
    
    # Align all series
    aligned_equity = {}
    for asset_name, prices in equity_data.items():
        aligned_equity[asset_name] = prices.loc[common_dates]
    
    aligned_fx = fx_rate.loc[common_dates]
    
    print(f"Data period: {common_dates[0]} to {common_dates[-1]}")
    print(f"Number of observations: {len(common_dates)}")
    
    # Calculate returns for Indian assets
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Indian Equity Performance: INR vs ILS Impact Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: INR/ILS Exchange Rate
    ax1 = axes[0, 0]
    fx_cumulative = calculate_cumulative_returns(aligned_fx)
    ax1.plot(fx_cumulative.index, fx_cumulative.values, 'red', linewidth=2, label='INR/ILS Rate')
    ax1.set_title('INR/ILS Exchange Rate (Normalized)', fontweight='bold')
    ax1.set_ylabel('Cumulative Change')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Calculate percentage change
    fx_total_change = (fx_cumulative.iloc[-1] - 1) * 100
    ax1.text(0.02, 0.95, f'Total Change: {fx_total_change:+.1f}%', 
             transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    # Show actual FX rate values
    start_rate = aligned_fx.iloc[0]
    end_rate = aligned_fx.iloc[-1]
    ax1.text(0.02, 0.85, f'Start: {start_rate:.4f} ILS/INR', 
             transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    ax1.text(0.02, 0.75, f'End: {end_rate:.4f} ILS/INR', 
             transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    
    # Plot 2: Indian Equities in INR terms
    ax2 = axes[0, 1]
    colors = ['blue', 'green', 'purple']
    
    inr_performance = {}
    for i, (asset_name, prices) in enumerate(aligned_equity.items()):
        inr_cumulative = calculate_cumulative_returns(prices)
        inr_performance[asset_name] = inr_cumulative
        ax2.plot(inr_cumulative.index, inr_cumulative.values, 
                colors[i % len(colors)], linewidth=2, label=asset_name.replace('_', ' '))
        
        # Show total return
        total_return = (inr_cumulative.iloc[-1] - 1) * 100
        print(f"{asset_name} INR return: {total_return:.1f}%")
    
    ax2.set_title('Indian Equities Performance (INR Terms)', fontweight='bold')
    ax2.set_ylabel('Cumulative Return')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Plot 3: Indian Equities in ILS terms
    ax3 = axes[1, 0]
    
    ils_performance = {}
    for i, (asset_name, prices) in enumerate(aligned_equity.items()):
        # Convert to ILS: multiply INR price by FX rate
        ils_prices = prices * aligned_fx
        ils_cumulative = calculate_cumulative_returns(ils_prices)
        ils_performance[asset_name] = ils_cumulative
        ax3.plot(ils_cumulative.index, ils_cumulative.values,
                colors[i % len(colors)], linewidth=2, label=asset_name.replace('_', ' '))
        
        # Show total return
        total_return = (ils_cumulative.iloc[-1] - 1) * 100
        print(f"{asset_name} ILS return: {total_return:.1f}%")
    
    ax3.set_title('Indian Equities Performance (ILS Terms)', fontweight='bold')
    ax3.set_ylabel('Cumulative Return')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot 4: Currency Impact Comparison
    ax4 = axes[1, 1]
    
    # Show the difference for NIFTY as example
    nifty_name = 'India_NIFTY'
    if nifty_name in inr_performance and nifty_name in ils_performance:
        inr_curve = inr_performance[nifty_name]
        ils_curve = ils_performance[nifty_name]
        
        ax4.plot(inr_curve.index, (inr_curve - 1) * 100, 'blue', linewidth=2, label='NIFTY 50 (INR)')
        ax4.plot(ils_curve.index, (ils_curve - 1) * 100, 'red', linewidth=2, label='NIFTY 50 (ILS)')
        ax4.plot(fx_cumulative.index, (fx_cumulative - 1) * 100, 'orange', linewidth=2, label='INR/ILS Rate', alpha=0.7)
        
        # Calculate currency drag
        inr_final = (inr_curve.iloc[-1] - 1) * 100
        ils_final = (ils_curve.iloc[-1] - 1) * 100
        currency_drag = ils_final - inr_final
        
        ax4.set_title('Currency Impact on NIFTY 50 Returns', fontweight='bold')
        ax4.set_ylabel('Cumulative Return (%)')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # Add text box with currency drag
        ax4.text(0.02, 0.95, f'Currency Drag: {currency_drag:+.1f}%', 
                transform=ax4.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('indian_currency_impact_analysis.png', dpi=300, bbox_inches='tight')
    print("Chart saved as 'indian_currency_impact_analysis.png'")
    
    # Don't show plot in headless environment
    # plt.show()
    
    # Summary statistics
    print("\n" + "="*80)
    print("INDIAN CURRENCY IMPACT SUMMARY")
    print("="*80)
    
    print(f"\nINR/ILS Exchange Rate:")
    print(f"  Start: {aligned_fx.iloc[0]:.4f} ILS per INR")
    print(f"  End: {aligned_fx.iloc[-1]:.4f} ILS per INR")
    print(f"  Total Change: {fx_total_change:+.1f}%")
    
    if fx_total_change > 0:
        print(f"  -> INR STRENGTHENED vs ILS (good for Indian equity returns in ILS)")
    else:
        print(f"  -> INR WEAKENED vs ILS (bad for Indian equity returns in ILS)")
    
    print(f"\nIndian Equity Performance Comparison:")
    for asset_name in aligned_equity.keys():
        if asset_name in inr_performance and asset_name in ils_performance:
            inr_ret = (inr_performance[asset_name].iloc[-1] - 1) * 100
            ils_ret = (ils_performance[asset_name].iloc[-1] - 1) * 100
            drag = ils_ret - inr_ret
            
            print(f"  {asset_name.replace('_', ' ')}:")
            print(f"    INR Return: {inr_ret:+.1f}%")
            print(f"    ILS Return: {ils_ret:+.1f}%") 
            print(f"    Currency Impact: {drag:+.1f}%")
    
    # Calculate annualized returns
    years = len(common_dates) / 250  # Assuming daily data, ~250 trading days per year
    print(f"\nAnnualized Returns (over {years:.1f} years):")
    for asset_name in aligned_equity.keys():
        if asset_name in inr_performance and asset_name in ils_performance:
            inr_total = (inr_performance[asset_name].iloc[-1] - 1)
            ils_total = (ils_performance[asset_name].iloc[-1] - 1)
            
            inr_annual = (1 + inr_total)**(1/years) - 1
            ils_annual = (1 + ils_total)**(1/years) - 1
            
            print(f"  {asset_name.replace('_', ' ')}:")
            print(f"    INR: {inr_annual:.1%} annually")
            print(f"    ILS: {ils_annual:.1%} annually")

if __name__ == "__main__":
    main()