"""
Adapter for Sortino Optimizer to work with website API

This adapter wraps the SortinoOptimizer to provide the same interface
and output format as the UnifiedPortfolioOptimizer.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional
import time

from .sortino_optimizer import SortinoOptimizer
from .ils_data_manager import ILSDataManager
from kyc.models import RiskProfile


@dataclass
class OptimizationResult:
    """Result format matching UnifiedPortfolioOptimizer output"""
    # Allocation results
    allocation_percentages: Dict[str, float]
    allocation_ils_amounts: Dict[str, float]
    
    # Portfolio metrics
    expected_return_annual: float
    volatility_annual: float
    sharpe_ratio: float
    cvar_95: float
    max_drawdown: float
    
    # Risk analysis
    risk_contributions: Dict[str, float]
    concentration_hhi: float
    
    # Additional fields expected by API
    total_investment_ils: float
    currency: str
    risk_free_rate_used: float
    optimization_success: bool
    optimization_time_ms: float
    risk_category: str
    composite_score: float

    # Performance history
    performance_history: Dict


class SortinoPortfolioOptimizer:
    """
    Drop-in replacement for UnifiedPortfolioOptimizer using Sortino optimization.
    
    This class provides the same interface as UnifiedPortfolioOptimizer but uses
    the simplified and more effective Sortino ratio optimization approach.
    """
    
    def __init__(self, data_manager: Optional[ILSDataManager] = None):
        """Initialize with data manager"""
        self.data_manager = data_manager or ILSDataManager()
        self.optimizer = SortinoOptimizer(self.data_manager)
        
    def optimize_portfolio(self, 
                          kyc_response: RiskProfile,
                          investment_amount: float,
                          investment_duration_years: float = 10.0) -> OptimizationResult:
        """
        Main optimization entry point matching UnifiedPortfolioOptimizer interface.
        
        Args:
            kyc_response: KYC risk profile from assessment
            investment_amount: Amount to invest in ILS
            investment_duration_years: Investment horizon
            
        Returns:
            OptimizationResult matching expected format
        """
        
        start_time = time.time()
        
        # Map KYC score to aggressiveness parameter (0 to 1)
        # KYC composite score is 0-100, we map to 0-1
        aggressiveness = kyc_response.composite_score / 100.0
        
        # Run Sortino optimization
        result = self.optimizer.optimize(aggressiveness)
        
        # Calculate ILS amounts for each asset
        allocation_ils_amounts = {}
        for asset, weight in result['weights'].items():
            allocation_ils_amounts[asset] = weight * investment_amount
            
        # Calculate risk contributions (simplified - proportional to weight * volatility)
        risk_contributions = self._calculate_risk_contributions(result['weights'])
        
        # Calculate concentration (HHI)
        weights_array = np.array(list(result['weights'].values()))
        concentration_hhi = np.sum(weights_array ** 2)
        
        # Calculate CVaR (using historical approach)
        cvar_95 = self._calculate_cvar(result['weights'])

        # Calculate historical performance
        performance_history = self.calculate_portfolio_performance(result['weights'], investment_amount)

        # Build result matching expected format
        optimization_time = (time.time() - start_time) * 1000
        
        return OptimizationResult(
            # Allocation results
            allocation_percentages=result['weights'],
            allocation_ils_amounts=allocation_ils_amounts,
            
            # Portfolio metrics
            expected_return_annual=result['expected_return'],
            volatility_annual=result['volatility'],
            sharpe_ratio=result['sharpe_ratio'],
            cvar_95=cvar_95,
            max_drawdown=result['max_drawdown'],
            
            # Risk analysis
            risk_contributions=risk_contributions,
            concentration_hhi=concentration_hhi,
            
            # Additional fields
            total_investment_ils=investment_amount,
            currency='ILS',
            risk_free_rate_used=self.data_manager.risk_free_rate.mean(),
            optimization_success=result.get('optimization_success', True),
            optimization_time_ms=optimization_time,
            risk_category=kyc_response.category_english,
            composite_score=kyc_response.composite_score,

            # Performance history
            performance_history=performance_history
        )
    
    def _calculate_risk_contributions(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate risk contribution of each asset to portfolio.
        
        Simplified approach: contribution proportional to weight * asset volatility
        """
        risk_contributions = {}
        total_risk = 0
        
        # First pass: calculate weighted risks
        for asset, weight in weights.items():
            if weight > 0.001 and asset in self.data_manager.returns_data.columns:
                asset_vol = self.data_manager.returns_data[asset].std() * np.sqrt(12)
                weighted_risk = weight * asset_vol
                risk_contributions[asset] = weighted_risk
                total_risk += weighted_risk
        
        # Second pass: normalize to sum to 1
        if total_risk > 0:
            for asset in risk_contributions:
                risk_contributions[asset] = risk_contributions[asset] / total_risk
                
        return risk_contributions
    
    def _calculate_cvar(self, weights: Dict[str, float]) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) at 95% confidence.
        
        CVaR is the expected loss in the worst 5% of cases.
        """
        # Create weight array aligned with returns data
        weight_array = np.zeros(len(self.data_manager.returns_data.columns))
        for i, asset in enumerate(self.data_manager.returns_data.columns):
            if asset in weights:
                weight_array[i] = weights[asset]
        
        # Calculate portfolio returns
        portfolio_returns = self.data_manager.returns_data @ weight_array
        
        # Calculate 5% VaR
        var_95 = portfolio_returns.quantile(0.05)
        
        # Calculate CVaR (expected value below VaR)
        cvar_returns = portfolio_returns[portfolio_returns <= var_95]
        if len(cvar_returns) > 0:
            cvar_monthly = cvar_returns.mean()
        else:
            cvar_monthly = var_95
            
        # Annualize (approximate)
        cvar_annual = cvar_monthly * np.sqrt(12)

        return abs(cvar_annual)  # Return as positive value

    def calculate_portfolio_performance(self, weights: Dict[str, float], investment_amount: float) -> Dict:
        """
        Calculate historical portfolio performance showing how the investment would have grown.

        Args:
            weights: Portfolio weights by asset
            investment_amount: Initial investment amount

        Returns:
            Dictionary with dates and portfolio values over time
        """
        # Create weight array aligned with returns data
        weight_array = np.zeros(len(self.data_manager.returns_data.columns))
        for i, asset in enumerate(self.data_manager.returns_data.columns):
            if asset in weights:
                weight_array[i] = weights[asset]

        # Calculate portfolio returns over time
        portfolio_returns = self.data_manager.returns_data @ weight_array

        # Calculate cumulative portfolio value starting with investment amount
        cumulative_returns = (1 + portfolio_returns).cumprod()
        portfolio_values = investment_amount * cumulative_returns

        # Create performance data with dates
        performance_data = {
            'dates': portfolio_returns.index.strftime('%Y-%m-%d').tolist(),
            'values': portfolio_values.tolist(),
            'returns': portfolio_returns.tolist(),
            'initial_investment': investment_amount,
            'final_value': portfolio_values.iloc[-1],
            'total_return_pct': ((portfolio_values.iloc[-1] / investment_amount) - 1) * 100,
            'years': len(portfolio_returns) / 12.0
        }

        return performance_data