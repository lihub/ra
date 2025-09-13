"""
Debug Return Calculation Issues

Compare the different stages of data processing to find where returns are getting lost.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_data_pipeline():
    """Analyze each step of the data processing pipeline"""
    
    print("="*80)
    print(" DEBUGGING RETURN CALCULATION PIPELINE")
    print("="*80)
    
    data_path = Path("processed_data")
    
    # Step 1: Load raw price data
    print("\n1. RAW PRICE DATA ANALYSIS")
    print("-" * 40)
    
    sp500_file = data_path / 'clean_US_Large_Cap_SP500.csv'
    fx_file = data_path / 'clean_USD_ILS_FX.csv'
    
    # Load SP500 prices
    sp500_df = pd.read_csv(sp500_file)
    sp500_df.columns = ['date', 'price']
    sp500_df['date'] = pd.to_datetime(sp500_df['date'])
    sp500_df = sp500_df.set_index('date').sort_index()
    
    # Load FX rate
    fx_df = pd.read_csv(fx_file)
    fx_df.columns = ['date', 'fx_rate']
    fx_df['date'] = pd.to_datetime(fx_df['date'])
    fx_df = fx_df.set_index('date').sort_index()
    
    print(f"SP500 price data:")
    print(f"  Period: {sp500_df.index[0]} to {sp500_df.index[-1]}")
    print(f"  Observations: {len(sp500_df)}")
    print(f"  Start price: {sp500_df['price'].iloc[0]:.2f}")
    print(f"  End price: {sp500_df['price'].iloc[-1]:.2f}")
    
    # Calculate raw price return
    total_price_return = (sp500_df['price'].iloc[-1] / sp500_df['price'].iloc[0]) - 1
    years = (sp500_df.index[-1] - sp500_df.index[0]).days / 365.25
    annualized_return = (1 + total_price_return)**(1/years) - 1
    
    print(f"  Total return: {total_price_return:.1%}")
    print(f"  Years: {years:.1f}")
    print(f"  Annualized return: {annualized_return:.1%}")
    
    # Step 2: Calculate monthly returns
    print(f"\n2. MONTHLY RETURN CALCULATION")
    print("-" * 40)
    
    sp500_df['monthly_return'] = sp500_df['price'].pct_change()
    sp500_returns = sp500_df['monthly_return'].dropna()
    
    print(f"Monthly returns:")
    print(f"  Count: {len(sp500_returns)}")
    print(f"  Mean: {sp500_returns.mean():.4f}")
    print(f"  Std: {sp500_returns.std():.4f}")
    print(f"  Min: {sp500_returns.min():.4f}")
    print(f"  Max: {sp500_returns.max():.4f}")
    
    # Annualize from monthly returns
    mean_monthly = sp500_returns.mean()
    annualized_from_monthly = (1 + mean_monthly)**12 - 1
    print(f"  Annualized (compound): {annualized_from_monthly:.1%}")
    print(f"  Annualized (simple): {mean_monthly * 12:.1%}")
    
    # Step 3: Currency conversion
    print(f"\n3. CURRENCY CONVERSION ANALYSIS")
    print("-" * 40)
    
    # Align dates
    common_dates = sp500_df.index.intersection(fx_df.index)
    sp500_aligned = sp500_df.loc[common_dates]
    fx_aligned = fx_df.loc[common_dates]
    
    print(f"FX rate data:")
    print(f"  Period: {fx_aligned.index[0]} to {fx_aligned.index[-1]}")
    print(f"  Start rate: {fx_aligned['fx_rate'].iloc[0]:.3f}")
    print(f"  End rate: {fx_aligned['fx_rate'].iloc[-1]:.3f}")
    
    fx_change = (fx_aligned['fx_rate'].iloc[-1] / fx_aligned['fx_rate'].iloc[0]) - 1
    print(f"  FX change: {fx_change:.1%}")
    
    # Convert to ILS prices
    ils_prices = sp500_aligned['price'] * fx_aligned['fx_rate']
    ils_total_return = (ils_prices.iloc[-1] / ils_prices.iloc[0]) - 1
    ils_years = (ils_prices.index[-1] - ils_prices.index[0]).days / 365.25
    ils_annualized = (1 + ils_total_return)**(1/ils_years) - 1
    
    print(f"ILS conversion:")
    print(f"  Start ILS price: {ils_prices.iloc[0]:.2f}")
    print(f"  End ILS price: {ils_prices.iloc[-1]:.2f}")
    print(f"  Total ILS return: {ils_total_return:.1%}")
    print(f"  Annualized ILS return: {ils_annualized:.1%}")
    
    # Step 4: What our system calculates
    print(f"\n4. SYSTEM CALCULATION COMPARISON")
    print("-" * 40)
    
    # Simulate our ILS data manager calculation
    ils_monthly_returns = ils_prices.pct_change().dropna()
    
    # Load risk-free rate
    rf_file = data_path / 'clean_Risk_Free_Rate_Israel.csv'
    rf_df = pd.read_csv(rf_file)
    rf_df.columns = ['date', 'rate']
    rf_df['date'] = pd.to_datetime(rf_df['date'])
    rf_df = rf_df.set_index('date').sort_index()
    
    # Align risk-free rate
    rf_aligned = rf_df.loc[ils_monthly_returns.index[0]:ils_monthly_returns.index[-1]]
    rf_aligned = rf_aligned.reindex(ils_monthly_returns.index, method='ffill')
    
    # Convert annual RF to monthly
    monthly_rf = (1 + rf_aligned['rate'])**(1/12) - 1
    
    print(f"Risk-free rate analysis:")
    print(f"  RF observations: {len(rf_aligned)}")
    print(f"  RF mean annual: {rf_aligned['rate'].mean():.2%}")
    print(f"  RF mean monthly: {monthly_rf.mean():.4f}")
    
    # Calculate excess returns
    excess_returns = ils_monthly_returns - monthly_rf
    
    print(f"Excess returns:")
    print(f"  Mean monthly excess: {excess_returns.mean():.4f}")
    print(f"  Annualized excess: {excess_returns.mean() * 12:.1%}")
    print(f"  Total return (excess + RF): {excess_returns.mean() * 12 + rf_aligned['rate'].mean():.1%}")
    
    # Step 5: Check data subset used by portfolio system
    print(f"\n5. PORTFOLIO SYSTEM DATA SUBSET")
    print("-" * 40)
    
    # Our system seems to use 2017-2025
    subset_start = '2017-10-31'
    subset_end = '2025-07-31'
    
    try:
        subset_ils = ils_monthly_returns.loc[subset_start:subset_end]
        subset_rf = rf_aligned.loc[subset_start:subset_end]
        subset_monthly_rf = (1 + subset_rf['rate'])**(1/12) - 1
        subset_excess = subset_ils - subset_monthly_rf
        
        print(f"Subset period: {subset_start} to {subset_end}")
        print(f"Subset observations: {len(subset_ils)}")
        print(f"Subset mean monthly return: {subset_ils.mean():.4f}")
        print(f"Subset annualized return: {(1 + subset_ils.mean())**12 - 1:.1%}")
        print(f"Subset excess return: {subset_excess.mean() * 12:.1%}")
        print(f"Subset total return: {subset_excess.mean() * 12 + subset_rf['rate'].mean():.1%}")
        
        # This should match what our portfolio system shows!
        
    except Exception as e:
        print(f"Error analyzing subset: {e}")
    
    print(f"\n" + "="*80)
    print(" SUMMARY OF FINDINGS")
    print("="*80)
    print(f"Full period SP500 return: {annualized_return:.1%} annually")
    print(f"Full period ILS return: {ils_annualized:.1%} annually") 
    print(f"Currency impact: {ils_annualized - annualized_return:.1%}")

if __name__ == "__main__":
    analyze_data_pipeline()