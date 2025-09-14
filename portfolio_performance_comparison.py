"""
Portfolio Performance Comparison Analysis

Creates a comprehensive comparison table showing:
1. Optimized portfolios for different risk categories
2. Single-asset strategies (S&P 500, NASDAQ, etc.)
3. Asset class weightings and performance metrics

Outputs results to CSV for analysis.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from kyc.risk_assessor import KYCRiskAssessor
from kyc.constants import RISK_CATEGORIES
from portfolio.unified_optimizer import UnifiedPortfolioOptimizer
import warnings
warnings.filterwarnings('ignore')

# Setup minimal logging
logging.basicConfig(level=logging.WARNING)

class PortfolioComparator:
    def __init__(self):
        self.optimizer = UnifiedPortfolioOptimizer()
        self.assessor = KYCRiskAssessor()
        
    def get_single_asset_performance(self, asset_name: str) -> Dict:
        """Calculate performance metrics for 100% allocation to single asset"""
        
        # Get asset data
        if asset_name not in self.optimizer.data_manager.returns_data.columns:
            return None
            
        returns = self.optimizer.data_manager.returns_data[asset_name]
        
        # Calculate key metrics
        annual_return = returns.mean() * 12  # Monthly to annual
        annual_vol = returns.std() * np.sqrt(12)  # Monthly to annual
        
        # Risk-free rate for Sharpe calculation (already annual)
        rf_rate = self.optimizer.data_manager.risk_free_rate.mean()
        sharpe = (annual_return - rf_rate) / annual_vol if annual_vol > 0 else 0
        
        # Maximum drawdown calculation
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # CVaR (95% confidence)
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        cvar_95_annual = cvar_95 * np.sqrt(12)  # Convert to annual
        
        return {
            'expected_return': annual_return,
            'volatility': annual_vol,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'cvar_95': cvar_95_annual,
            'allocation': {asset_name: 1.0}  # 100% allocation
        }
    
    def get_optimized_portfolio_performance(self, risk_category: str) -> Dict:
        """Get performance for optimized portfolio of given risk category"""
        
        # Create responses that map to this category
        if risk_category == 'ultra_conservative':
            responses = {
                "horizon_score": 20, "loss_tolerance": 10, "experience_score": 50,
                "financial_score": 30, "goal_score": 10, "sleep_score": 5
            }
        elif risk_category == 'conservative':
            responses = {
                "horizon_score": 30, "loss_tolerance": 30, "experience_score": 50,
                "financial_score": 50, "goal_score": 30, "sleep_score": 20
            }
        elif risk_category == 'moderate':
            responses = {
                "horizon_score": 50, "loss_tolerance": 50, "experience_score": 60,
                "financial_score": 60, "goal_score": 60, "sleep_score": 40
            }
        elif risk_category == 'aggressive':
            responses = {
                "horizon_score": 80, "loss_tolerance": 80, "experience_score": 70,
                "financial_score": 75, "goal_score": 80, "sleep_score": 70
            }
        elif risk_category == 'very_aggressive':
            responses = {
                "horizon_score": 100, "loss_tolerance": 100, "experience_score": 90,
                "financial_score": 100, "goal_score": 100, "sleep_score": 90
            }
        else:  # ultra_aggressive - maximally aggressive
            responses = {
                "horizon_score": 100, "loss_tolerance": 100, "experience_score": 100,
                "financial_score": 100, "goal_score": 100, "sleep_score": 100
            }
        
        # Process KYC
        kyc_result = self.assessor.process_responses(responses)
        
        # Optimize portfolio
        result = self.optimizer.optimize_portfolio(
            kyc_response=kyc_result,
            investment_amount=100000,  # Standard amount for comparison
            investment_duration_years=20
        )
        
        return {
            'expected_return': result.expected_return_annual,
            'volatility': result.volatility_annual,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'cvar_95': result.cvar_95,
            'allocation': result.allocation_percentages,
            'category_name': kyc_result.category_english
        }
    
    def aggregate_by_asset_class(self, allocation: Dict[str, float]) -> Dict[str, float]:
        """Aggregate asset allocations by asset class"""
        
        class_allocation = {}
        
        for asset, weight in allocation.items():
            metadata = self.optimizer.data_manager.asset_metadata.get(asset)
            if metadata:
                asset_class = metadata.category
            else:
                asset_class = 'other'
            
            class_allocation[asset_class] = class_allocation.get(asset_class, 0) + weight
        
        return class_allocation
    
    def create_comparison_table(self) -> pd.DataFrame:
        """Create comprehensive comparison table"""
        
        print("Creating portfolio performance comparison...")
        
        results = []
        all_assets = set()  # Track all possible assets for columns
        
        # Get top single-asset strategies
        top_assets = [
            'NASDAQ_Total_Return',
            'US_Large_Cap_SP500',
            'Israel_TA125',
            'Gold_Futures',
            'India_NIFTY',
            'Germany_DAX',
            'US_REIT_Select'
        ]
        
        print("Calculating single-asset strategies...")
        for asset in top_assets:
            perf = self.get_single_asset_performance(asset)
            if perf:
                all_assets.update(perf['allocation'].keys())
                
                result_row = {
                    'Strategy_Type': 'Single Asset',
                    'Strategy_Name': asset.replace('_', ' '),
                    'Expected_Return': perf['expected_return'],
                    'Volatility': perf['volatility'],
                    'Sharpe_Ratio': perf['sharpe_ratio'],
                    'Max_Drawdown': perf['max_drawdown'],
                    'CVaR_95': perf['cvar_95'],
                }
                # Add individual asset allocations
                for asset_name in perf['allocation']:
                    result_row[f'{asset_name}_%'] = perf['allocation'][asset_name] * 100
                
                results.append(result_row)
        
        print("Calculating optimized portfolios...")
        # Get optimized portfolios for each risk category (including ultra-aggressive)
        risk_categories = ['ultra_conservative', 'conservative', 'moderate', 'aggressive', 'very_aggressive', 'ultra_aggressive']
        
        for risk_category in risk_categories:
            try:
                perf = self.get_optimized_portfolio_performance(risk_category)
                all_assets.update(perf['allocation'].keys())
                
                result_row = {
                    'Strategy_Type': 'Optimized Portfolio',
                    'Strategy_Name': perf['category_name'],
                    'Expected_Return': perf['expected_return'],
                    'Volatility': perf['volatility'],
                    'Sharpe_Ratio': perf['sharpe_ratio'],
                    'Max_Drawdown': perf['max_drawdown'],
                    'CVaR_95': perf['cvar_95'],
                }
                # Add individual asset allocations
                for asset_name in perf['allocation']:
                    result_row[f'{asset_name}_%'] = perf['allocation'][asset_name] * 100
                
                results.append(result_row)
                
            except Exception as e:
                print(f"Error processing {risk_category}: {str(e)[:100]}")
                continue
        
        # Create DataFrame and fill missing asset allocations with 0
        df = pd.DataFrame(results)
        
        # Ensure all asset columns exist and fill with 0 where missing
        for asset in all_assets:
            col_name = f'{asset}_%'
            if col_name not in df.columns:
                df[col_name] = 0.0
            else:
                df[col_name] = df[col_name].fillna(0.0)
        
        # Sort by expected return (descending)
        df = df.sort_values('Expected_Return', ascending=False)
        
        # Format percentage columns (performance metrics only, asset allocations already in %)
        percentage_cols = ['Expected_Return', 'Volatility', 'Max_Drawdown', 'CVaR_95']
        
        for col in percentage_cols:
            if col in df.columns:
                df[col] = df[col] * 100
        
        return df
    
    def print_summary(self, df: pd.DataFrame):
        """Print summary insights"""
        
        print("\n" + "="*80)
        print(" PORTFOLIO PERFORMANCE COMPARISON ANALYSIS")
        print("="*80)
        
        # Best performing strategies
        print("\nTOP 5 STRATEGIES BY EXPECTED RETURN:")
        print("-" * 50)
        top5 = df.head(5)
        for idx, row in top5.iterrows():
            print(f"{row['Strategy_Name']:<25} {row['Expected_Return']:6.1f}% return, {row['Volatility']:5.1f}% vol, {row['Sharpe_Ratio']:4.2f} Sharpe")
        
        # Best risk-adjusted returns
        print(f"\nTOP 5 STRATEGIES BY SHARPE RATIO:")
        print("-" * 50)
        top_sharpe = df.nlargest(5, 'Sharpe_Ratio')
        for idx, row in top_sharpe.iterrows():
            print(f"{row['Strategy_Name']:<25} {row['Sharpe_Ratio']:4.2f} Sharpe, {row['Expected_Return']:6.1f}% return, {row['Volatility']:5.1f}% vol")
        
        # Compare single assets vs optimized
        single_assets = df[df['Strategy_Type'] == 'Single Asset']
        optimized = df[df['Strategy_Type'] == 'Optimized Portfolio']
        
        print(f"\nSINGLE ASSET vs OPTIMIZED PORTFOLIO COMPARISON:")
        print("-" * 50)
        print(f"Single Assets - Avg Return: {single_assets['Expected_Return'].mean():.1f}%, Avg Vol: {single_assets['Volatility'].mean():.1f}%")
        print(f"Optimized    - Avg Return: {optimized['Expected_Return'].mean():.1f}%, Avg Vol: {optimized['Volatility'].mean():.1f}%")
        
        best_single = single_assets.iloc[0] if not single_assets.empty else None
        best_optimized = optimized.nlargest(1, 'Expected_Return').iloc[0] if not optimized.empty else None
        
        if best_single is not None and best_optimized is not None:
            print(f"\nBEST SINGLE ASSET: {best_single['Strategy_Name']}")
            print(f"  Return: {best_single['Expected_Return']:.1f}%, Vol: {best_single['Volatility']:.1f}%, Sharpe: {best_single['Sharpe_Ratio']:.2f}")
            
            print(f"\nBEST OPTIMIZED: {best_optimized['Strategy_Name']}")
            print(f"  Return: {best_optimized['Expected_Return']:.1f}%, Vol: {best_optimized['Volatility']:.1f}%, Sharpe: {best_optimized['Sharpe_Ratio']:.2f}")

def main():
    """Main execution"""
    
    comparator = PortfolioComparator()
    
    # Create comparison table
    df = comparator.create_comparison_table()
    
    # Save to CSV
    output_file = 'detailed_portfolio_comparison.csv'
    df.to_csv(output_file, index=False, float_format='%.2f', encoding='utf-8')
    
    print(f"\nResults saved to: {output_file}")
    
    # Print summary analysis
    comparator.print_summary(df)
    
    print(f"\n{'='*80}")
    print(" KEY FINDINGS")
    print("="*80)
    
    # Find if any optimized portfolio beats S&P 500
    sp500_row = df[df['Strategy_Name'].str.contains('SP500', na=False)]
    if not sp500_row.empty:
        sp500_return = sp500_row.iloc[0]['Expected_Return']
        better_optimized = df[(df['Strategy_Type'] == 'Optimized Portfolio') & 
                             (df['Expected_Return'] > sp500_return)]
        
        if better_optimized.empty:
            print(f"\n[X] NO OPTIMIZED PORTFOLIO BEATS S&P 500")
            print(f"   S&P 500: {sp500_return:.1f}% annual return")
            print(f"   Best optimized: {df[df['Strategy_Type'] == 'Optimized Portfolio']['Expected_Return'].max():.1f}% annual return")
        else:
            print(f"\n[OK] {len(better_optimized)} OPTIMIZED PORTFOLIOS BEAT S&P 500")
            for idx, row in better_optimized.iterrows():
                print(f"   {row['Strategy_Name']}: {row['Expected_Return']:.1f}% vs S&P 500: {sp500_return:.1f}%")
    
    print(f"\nFull comparison table saved to: {output_file}")

if __name__ == "__main__":
    main()