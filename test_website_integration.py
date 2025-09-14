"""
Test Website Integration with Sortino Optimizer

Verifies that the new SortinoPortfolioOptimizer works correctly
with the website's API expectations.
"""

from portfolio.sortino_adapter import SortinoPortfolioOptimizer
from kyc.risk_assessor import KYCRiskAssessor
import json

def test_integration():
    """Test the integration of Sortino optimizer with website API"""
    
    print("="*60)
    print(" TESTING WEBSITE INTEGRATION WITH SORTINO OPTIMIZER")
    print("="*60)
    
    # Create test KYC responses for different risk levels
    test_cases = [
        {
            "name": "Conservative Investor",
            "responses": {
                "horizon_score": 30,
                "loss_tolerance": 30,
                "experience_score": 50,
                "financial_score": 50,
                "goal_score": 30,
                "sleep_score": 20
            },
            "investment": 100000,
            "duration": 10
        },
        {
            "name": "Aggressive Investor",
            "responses": {
                "horizon_score": 80,
                "loss_tolerance": 80,
                "experience_score": 70,
                "financial_score": 75,
                "goal_score": 80,
                "sleep_score": 70
            },
            "investment": 250000,
            "duration": 20
        }
    ]
    
    # Initialize components
    assessor = KYCRiskAssessor()
    optimizer = SortinoPortfolioOptimizer()
    
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f" {test['name']}")
        print("="*50)
        
        # Process KYC
        kyc_result = assessor.process_responses(test['responses'])
        print(f"KYC Category: {kyc_result.category_english}")
        print(f"Risk Score: {kyc_result.composite_score:.1f}")
        
        # Run optimization
        try:
            result = optimizer.optimize_portfolio(
                kyc_response=kyc_result,
                investment_amount=test['investment'],
                investment_duration_years=test['duration']
            )
            
            # Check all required fields exist
            print("\nRequired Fields Check:")
            required_fields = [
                'allocation_percentages', 'allocation_ils_amounts',
                'expected_return_annual', 'volatility_annual', 'sharpe_ratio',
                'cvar_95', 'max_drawdown', 'risk_contributions',
                'concentration_hhi', 'total_investment_ils', 'currency',
                'risk_free_rate_used', 'optimization_success',
                'optimization_time_ms', 'risk_category'
            ]
            
            for field in required_fields:
                if hasattr(result, field):
                    print(f"  [OK] {field}")
                else:
                    print(f"  [X] {field} MISSING!")
            
            # Display results
            print(f"\nOptimization Results:")
            print(f"  Success: {result.optimization_success}")
            print(f"  Expected Return: {result.expected_return_annual*100:.1f}%")
            print(f"  Volatility: {result.volatility_annual*100:.1f}%")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  CVaR 95%: {result.cvar_95*100:.1f}%")
            print(f"  Max Drawdown: {result.max_drawdown*100:.1f}%")
            print(f"  HHI Concentration: {result.concentration_hhi:.3f}")
            
            # Top allocations
            print(f"\nTop Allocations:")
            sorted_alloc = sorted(result.allocation_percentages.items(), 
                                key=lambda x: x[1], reverse=True)
            for asset, weight in sorted_alloc[:3]:
                if weight > 0.01:
                    amount = result.allocation_ils_amounts[asset]
                    print(f"  {asset}: {weight*100:.1f}% (₪{amount:,.0f})")
            
            # Simulate API response structure (what main.py returns)
            api_response = {
                "risk_assessment": {
                    "category": kyc_result.category_english,
                    "composite_score": kyc_result.composite_score,
                },
                "portfolio_allocation": {
                    "percentages": result.allocation_percentages,
                    "amounts_ils": result.allocation_ils_amounts,
                },
                "performance_metrics": {
                    "expected_return_annual": round(result.expected_return_annual * 100, 2),
                    "volatility_annual": round(result.volatility_annual * 100, 2),
                    "sharpe_ratio": round(result.sharpe_ratio, 2),
                }
            }
            
            # Verify JSON serializable
            try:
                json.dumps(api_response)
                print("\n[OK] API response is JSON serializable")
            except Exception as e:
                print(f"\n[X] JSON serialization error: {e}")
                
        except Exception as e:
            print(f"\n[X] ERROR: {e}")
            import traceback
            traceback.print_exc()
            
    print("\n" + "="*60)
    print(" INTEGRATION TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_integration()