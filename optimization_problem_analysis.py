"""
Optimization Problem Analysis for Aggressive Investors

Shows exactly what optimization problem is being solved and why it's failing
"""

import numpy as np
from kyc.risk_assessor import KYCRiskAssessor
from portfolio.unified_optimizer import UnifiedPortfolioOptimizer, map_kyc_to_optimization_params

def analyze_optimization_problem():
    """Analyze the optimization problem for aggressive investors"""
    
    print("="*80)
    print(" OPTIMIZATION PROBLEM ANALYSIS FOR AGGRESSIVE INVESTORS")
    print("="*80)
    
    # Create aggressive investor profile
    aggressive_responses = {
        "horizon_score": 80,
        "loss_tolerance": 80,
        "experience_score": 70,
        "financial_score": 75,
        "goal_score": 80,
        "sleep_score": 70
    }
    
    very_aggressive_responses = {
        "horizon_score": 100,
        "loss_tolerance": 100,
        "experience_score": 100,
        "financial_score": 100,
        "goal_score": 100,
        "sleep_score": 100
    }
    
    # Process KYC
    assessor = KYCRiskAssessor()
    aggressive_kyc = assessor.process_responses(aggressive_responses)
    very_aggressive_kyc = assessor.process_responses(very_aggressive_responses)
    
    # Get optimization parameters
    aggressive_params = map_kyc_to_optimization_params(aggressive_kyc)
    very_aggressive_params = map_kyc_to_optimization_params(very_aggressive_kyc)
    
    print("\n" + "="*80)
    print(" AGGRESSIVE INVESTOR (Score: 75)")
    print("="*80)
    print_optimization_details(aggressive_params)
    
    print("\n" + "="*80)
    print(" VERY AGGRESSIVE INVESTOR (Score: 100)")
    print("="*80)
    print_optimization_details(very_aggressive_params)
    
    # Load actual data to show what's available
    optimizer = UnifiedPortfolioOptimizer()
    
    print("\n" + "="*80)
    print(" AVAILABLE ASSETS AND THEIR PERFORMANCE")
    print("="*80)
    
    # Get asset performance
    assets_data = []
    for asset in optimizer.data_manager.get_asset_names():
        returns = optimizer.data_manager.returns_data[asset]
        annual_return = returns.mean() * 12
        annual_vol = returns.std() * np.sqrt(12)
        rf = optimizer.data_manager.risk_free_rate.mean()
        sharpe = (annual_return - rf) / annual_vol if annual_vol > 0 else 0
        
        assets_data.append({
            'name': asset,
            'return': annual_return,
            'volatility': annual_vol,
            'sharpe': sharpe
        })
    
    # Sort by return
    assets_data.sort(key=lambda x: x['return'], reverse=True)
    
    print("\nTop 10 Assets by Return:")
    print(f"{'Asset':<30} {'Return':>10} {'Volatility':>12} {'Sharpe':>10}")
    print("-"*65)
    for asset in assets_data[:10]:
        print(f"{asset['name']:<30} {asset['return']*100:>9.1f}% {asset['volatility']*100:>11.1f}% {asset['sharpe']:>10.2f}")
    
    print("\n" + "="*80)
    print(" KEY ISSUES WITH THE OPTIMIZATION")
    print("="*80)
    
    print("""
1. UTILITY FUNCTION STRUCTURE:
   Utility = Return - lambda*Vol^2 - alpha*CVaR - beta*VolPenalty - gamma*Concentration + delta*Skewness
   
   For Aggressive (score=75):
   - lambda (risk aversion) = 2.5  [High penalty on variance!]
   - alpha (CVaR penalty) = 2.4   [High penalty on tail risk!]
   - beta (vol penalty) = 2.25   [Penalty for exceeding target vol]
   - gamma (concentration) = 0.95 [Still penalizes concentration]
   
2. CONSTRAINT ISSUES:
   - Max single asset: 35% (even for very aggressive!)
   - Equity range: 55-80% (forces diversification into bonds)
   - CVaR constraint: Max 28% (limits high-vol assets)
   - Volatility constraint: Max 20% (S&P is 12.7%, NASDAQ is 15.7%)

3. THE CORE PROBLEM:
   The optimizer is using QUADRATIC PENALTY on volatility (Vol^2), which means:
   - NASDAQ (15.7% vol) gets penalty of: 2.5 * 0.157^2 = 0.062 = 6.2% penalty
   - This 6.2% penalty nearly wipes out NASDAQ's return advantage!
   - Lower-vol assets with lower returns look artificially attractive
   
4. WHY IT PICKS JAPAN/EM OVER NASDAQ:
   - Japan MSCI: Lower volatility, so less quadratic penalty
   - Emerging Markets: Provides "diversification" which reduces portfolio vol
   - The optimizer values VOL REDUCTION more than RETURN MAXIMIZATION
   
5. THE FIX NEEDED:
   For aggressive investors:
   - Reduce λ (risk aversion) to 0.5 or less
   - Increase max single asset to 50-60%
   - Use linear vol penalty, not quadratic
   - Focus on Sharpe ratio, not just volatility
""")

def print_optimization_details(params):
    """Print optimization parameters in detail"""
    
    print("\nOBJECTIVE FUNCTION PARAMETERS:")
    print(f"  Risk Aversion (lambda):      {params.risk_aversion_lambda:.2f}")
    print(f"  CVaR Penalty (alpha):        {params.cvar_penalty_alpha:.2f}")
    print(f"  Vol Target Penalty (beta):   {params.vol_penalty_beta:.2f}")
    print(f"  Concentration Penalty (gamma): {params.concentration_penalty_gamma:.2f}")
    print(f"  Skewness Reward (delta):     {params.skewness_reward_delta:.2f}")
    
    print("\nTARGETS (Soft Constraints):")
    print(f"  Target Volatility:           {params.target_volatility*100:.1f}%")
    print(f"  Target CVaR:                 {params.target_cvar*100:.1f}%")
    
    print("\nHARD CONSTRAINTS:")
    print(f"  Max Volatility:              {params.max_volatility*100:.1f}%")
    print(f"  Max CVaR:                    {params.max_cvar*100:.1f}%")
    print(f"  Equity Range:                {params.equity_range[0]*100:.0f}%-{params.equity_range[1]*100:.0f}%")
    print(f"  Max Single Asset:            {params.max_single_asset*100:.0f}%")
    
    print("\nOPTIMIZATION PROBLEM:")
    print(f"  MAXIMIZE: Return - {params.risk_aversion_lambda:.1f}*Vol² - {params.cvar_penalty_alpha:.1f}*CVaR")
    print(f"            - {params.vol_penalty_beta:.1f}*(Vol-Target)² - {params.concentration_penalty_gamma:.1f}*HHI")
    print(f"            + {params.skewness_reward_delta:.1f}*Skewness")

if __name__ == "__main__":
    analyze_optimization_problem()