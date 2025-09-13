"""
Show Portfolio Examples - Typical Investor Cases

Demonstrates portfolio allocations and expected performance
for different investor profiles.
"""

import logging
from tabulate import tabulate
from kyc.risk_assessor import KYCRiskAssessor
from portfolio.unified_optimizer import UnifiedPortfolioOptimizer
import warnings
warnings.filterwarnings('ignore')

# Setup minimal logging
logging.basicConfig(level=logging.WARNING)

def format_percentage(value):
    """Format as percentage"""
    return f"{value*100:.1f}%"

def format_currency(value):
    """Format as currency"""
    return f"ILS {value:,.0f}"

def show_portfolio_results(profile_name, responses, investment_amount, duration):
    """Show portfolio results for a given profile"""
    
    print(f"\n{'='*80}")
    print(f"INVESTOR PROFILE: {profile_name}")
    print(f"{'='*80}")
    
    # Process KYC
    assessor = KYCRiskAssessor()
    kyc_result = assessor.process_responses(responses)
    
    print(f"\nRisk Assessment:")
    print(f"  Category: {kyc_result.category_english}")
    print(f"  Risk Score: {kyc_result.composite_score:.1f}/100")
    print(f"  Risk Level: {kyc_result.risk_level}/10")
    print(f"  Max Drawdown Tolerance: {format_percentage(kyc_result.max_drawdown)}")
    print(f"  Target Volatility: {format_percentage(kyc_result.target_volatility)}")
    
    # Optimize portfolio
    optimizer = UnifiedPortfolioOptimizer()
    result = optimizer.optimize_portfolio(
        kyc_response=kyc_result,
        investment_amount=investment_amount,
        investment_duration_years=duration
    )
    
    print(f"\nInvestment Details:")
    print(f"  Amount: {format_currency(investment_amount)}")
    print(f"  Time Horizon: {duration} years")
    print(f"  Optimization Time: {result.optimization_time_ms:.0f}ms")
    
    print(f"\nExpected Performance:")
    print(f"  Annual Return: {format_percentage(result.expected_return_annual)}")
    print(f"  Annual Volatility: {format_percentage(result.volatility_annual)}")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"  95% CVaR (Tail Risk): {format_percentage(result.cvar_95)}")
    print(f"  Maximum Drawdown: {format_percentage(result.max_drawdown)}")
    
    # Portfolio allocation table
    print(f"\nPortfolio Allocation:")
    
    # Sort by weight
    sorted_assets = sorted(result.allocation_percentages.items(), 
                          key=lambda x: x[1], reverse=True)
    
    # Prepare table data
    table_data = []
    for asset, weight in sorted_assets[:10]:  # Top 10 holdings
        ils_amount = result.allocation_ils_amounts[asset]
        table_data.append([
            asset.replace('_', ' '),
            format_percentage(weight),
            format_currency(ils_amount)
        ])
    
    # Add total row if more than 10 assets
    if len(sorted_assets) > 10:
        remaining_weight = sum(w for _, w in sorted_assets[10:])
        remaining_amount = sum(result.allocation_ils_amounts[a] for a, _ in sorted_assets[10:])
        table_data.append(['...', '...', '...'])
        table_data.append([
            f"Other {len(sorted_assets)-10} assets",
            format_percentage(remaining_weight),
            format_currency(remaining_amount)
        ])
    
    # Add total
    table_data.append(['='*30, '='*10, '='*15])
    table_data.append([
        'TOTAL',
        format_percentage(sum(result.allocation_percentages.values())),
        format_currency(investment_amount)
    ])
    
    print(tabulate(table_data, 
                  headers=['Asset', 'Weight', 'Amount (ILS)'],
                  tablefmt='grid'))
    
    # Category breakdown
    print(f"\nAsset Class Distribution:")
    category_breakdown = {}
    for asset, weight in result.allocation_percentages.items():
        metadata = optimizer.data_manager.asset_metadata.get(asset)
        if metadata:
            category = metadata.category
        else:
            category = 'other'
        category_breakdown[category] = category_breakdown.get(category, 0) + weight
    
    category_data = []
    for category, weight in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
        category_data.append([
            category.capitalize(),
            format_percentage(weight)
        ])
    
    print(tabulate(category_data,
                  headers=['Asset Class', 'Allocation'],
                  tablefmt='simple'))
    
    return result

def main():
    """Run portfolio examples for typical cases"""
    
    print("\n" + "="*80)
    print(" PORTFOLIO OPTIMIZATION EXAMPLES - TYPICAL INVESTOR CASES")
    print("="*80)
    
    # Define typical investor profiles
    profiles = [
        {
            "name": "YOUNG PROFESSIONAL (28 years old, first investment)",
            "responses": {
                "horizon_score": 80,      # Long-term (retirement in 35+ years)
                "loss_tolerance": 70,     # Can tolerate volatility
                "experience_score": 20,   # Limited experience
                "financial_score": 60,    # Good income, can invest 15% monthly
                "goal_score": 80,         # Growth-focused
                "sleep_score": 50         # Moderate comfort with risk
            },
            "amount": 50000,
            "duration": 30
        },
        {
            "name": "MIDDLE-AGED COUPLE (45 years old, saving for retirement)",
            "responses": {
                "horizon_score": 50,      # 15-20 years to retirement
                "loss_tolerance": 50,     # Moderate risk tolerance
                "experience_score": 70,   # Experienced investors
                "financial_score": 75,    # High income, substantial savings
                "goal_score": 60,         # Balanced growth
                "sleep_score": 40         # Cautious about large losses
            },
            "amount": 500000,
            "duration": 15
        },
        {
            "name": "RETIREE (65 years old, preserving wealth)",
            "responses": {
                "horizon_score": 20,      # Short-term needs
                "loss_tolerance": 10,     # Cannot afford losses
                "experience_score": 80,   # Very experienced
                "financial_score": 30,    # Fixed income, limited new savings
                "goal_score": 10,         # Capital preservation
                "sleep_score": 5          # Very risk-averse
            },
            "amount": 1000000,
            "duration": 5
        },
        {
            "name": "AGGRESSIVE TECH ENTREPRENEUR (35 years old)",
            "responses": {
                "horizon_score": 100,     # Very long-term
                "loss_tolerance": 100,    # Comfortable buying dips
                "experience_score": 90,   # Sophisticated investor
                "financial_score": 100,   # High income, high savings rate
                "goal_score": 100,        # Maximum growth
                "sleep_score": 90         # High risk tolerance
            },
            "amount": 250000,
            "duration": 25
        },
        {
            "name": "CONSERVATIVE SAVER (50 years old, risk-averse)",
            "responses": {
                "horizon_score": 30,      # 10 years to retirement
                "loss_tolerance": 20,     # Uncomfortable with volatility
                "experience_score": 40,   # Some experience
                "financial_score": 50,    # Moderate income
                "goal_score": 30,         # Modest growth with safety
                "sleep_score": 10         # Loses sleep over 10% drops
            },
            "amount": 200000,
            "duration": 10
        }
    ]
    
    # Process each profile
    all_results = []
    for profile in profiles:
        result = show_portfolio_results(
            profile["name"],
            profile["responses"],
            profile["amount"],
            profile["duration"]
        )
        all_results.append((profile["name"], result))
    
    # Summary comparison
    print("\n" + "="*80)
    print(" PORTFOLIO COMPARISON SUMMARY")
    print("="*80)
    
    comparison_data = []
    for name, result in all_results:
        # Simplify name for table
        if "YOUNG PROFESSIONAL" in name:
            short_name = "Young Professional"
        elif "MIDDLE-AGED" in name:
            short_name = "Middle-Aged Couple"
        elif "RETIREE" in name:
            short_name = "Retiree"
        elif "ENTREPRENEUR" in name:
            short_name = "Tech Entrepreneur"
        else:
            short_name = "Conservative Saver"
            
        comparison_data.append([
            short_name,
            result.risk_category,
            format_percentage(result.expected_return_annual),
            format_percentage(result.volatility_annual),
            f"{result.sharpe_ratio:.2f}",
            format_percentage(result.cvar_95)
        ])
    
    print(tabulate(comparison_data,
                  headers=['Investor', 'Risk Category', 'Return', 'Volatility', 'Sharpe', 'Tail Risk'],
                  tablefmt='grid'))
    
    print("\n" + "="*80)
    print(" KEY INSIGHTS")
    print("="*80)
    
    print("""
1. DIVERSIFICATION: All portfolios are well-diversified across asset classes
   - Even aggressive portfolios maintain some bond allocation
   - Conservative portfolios still include small equity positions
   
2. RISK-RETURN TRADEOFF: Higher risk tolerance leads to:
   - Higher expected returns but also higher volatility
   - Greater equity allocation (up to 80-90% for aggressive)
   - Higher tail risk (CVaR) exposure
   
3. TIME HORIZON IMPACT:
   - Longer horizons allow for more equity exposure
   - Short horizons force conservative allocations regardless of risk tolerance
   
4. ISRAELI MARKET INTEGRATION:
   - All portfolios include Israeli government bonds for stability
   - Currency risk managed through ILS-denominated assets
   - International diversification balanced with home bias
    """)

if __name__ == "__main__":
    main()