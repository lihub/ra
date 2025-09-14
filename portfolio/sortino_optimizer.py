"""
Simplified Portfolio Optimizer - Sortino Ratio Maximization

A clean, simple optimizer that:
1. Maximizes Sortino ratio (return over downside risk)
2. Uses simple weight constraints based on aggressiveness
3. Respects maximum drawdown limits

This replaces the overly complex utility function approach.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class AssetClassification:
    """Classification of assets by risk level"""
    high_risk_equity = [
        'NASDAQ_Total_Return', 'US_Small_Cap_Russell2000', 
        'India_NIFTY', 'Israel_SME60', 'Emerging_Markets_MSCI'
    ]
    
    medium_risk_equity = [
        'US_Large_Cap_SP500', 'Germany_DAX', 'France_CAC40',
        'UK_FTSE100', 'Europe_MSCI', 'Japan_MSCI', 'Israel_TA125'
    ]
    
    low_risk_equity = [
        'US_REIT_Select'
    ]
    
    safe_bonds = [
        'Israel_Gov_Indexed_0_2Y', 'Israel_Gov_Indexed_5_10Y',
        'Israel_Gov_Shekel_0_2Y', 'Israel_Gov_Shekel_5_10Y',
        'Israel_TelBond_60', 'Israel_TelBond_Shekel',
        'US_Gov_Bonds_3_7Y', 'US_Gov_Bonds_Short'
    ]
    
    commodities = [
        'Gold_Futures', 'Oil_Brent_Futures'
    ]
    
    @classmethod
    def get_asset_class(cls, asset_name: str) -> str:
        """Get risk class for an asset"""
        if asset_name in cls.high_risk_equity:
            return 'high_risk_equity'
        elif asset_name in cls.medium_risk_equity:
            return 'medium_risk_equity'
        elif asset_name in cls.low_risk_equity:
            return 'low_risk_equity'
        elif asset_name in cls.safe_bonds:
            return 'safe_bonds'
        elif asset_name in cls.commodities:
            return 'commodities'
        else:
            return 'unknown'


class SortinoOptimizer:
    """Simplified portfolio optimizer using Sortino ratio"""
    
    def __init__(self, data_manager):
        """Initialize with data manager"""
        self.data_manager = data_manager
        self.returns_data = data_manager.returns_data
        self.risk_free_rate = data_manager.risk_free_rate.mean()
        
    def calculate_weight_limit(self, aggressiveness: float, asset_name: str) -> float:
        """
        Calculate maximum weight for an asset based on aggressiveness.
        
        F(s, asset_class) where s is aggressiveness (0 to 1)
        - s=1: F=1.0 for top equity (can go 100% in NASDAQ/S&P)
        - s=0: F=0.05 for risky, 0.30 for safe (conservative must diversify)
        """
        s = aggressiveness
        asset_class = AssetClassification.get_asset_class(asset_name)
        
        # Special handling for top performers
        if asset_name in ['NASDAQ_Total_Return', 'US_Large_Cap_SP500']:
            # Allow up to 100% for ultra-aggressive in top performers
            return 0.10 + 0.90 * s
        
        if asset_class == 'high_risk_equity':
            # For risky assets: 5% at s=0, 80% at s=1
            return 0.05 + 0.75 * s
            
        elif asset_class == 'medium_risk_equity':
            # For medium risk: 10% at s=0, 80% at s=1
            return 0.10 + 0.70 * s
            
        elif asset_class == 'low_risk_equity':
            # For low risk equity: 15% at s=0, 70% at s=1
            return 0.15 + 0.55 * s
            
        elif asset_class == 'safe_bonds':
            # For bonds: 30% at s=0, 50% at s=1 (less for aggressive)
            return 0.30 + 0.20 * s
            
        elif asset_class == 'commodities':
            # For commodities: 10% at s=0, 20% at s=1 (limit commodity for aggressive)
            # Aggressive investors should focus on equity, not commodities
            if s >= 0.8:
                return 0.20  # Max 20% in commodities for aggressive
            else:
                return 0.10 + 0.25 * s
            
        else:
            # Unknown assets: conservative limits
            return 0.05 + 0.25 * s
    
    def calculate_max_drawdown_limit(self, aggressiveness: float) -> float:
        """
        Calculate maximum drawdown tolerance based on aggressiveness.
        
        Y(s) where s is aggressiveness (0 to 1)
        - s=0: Y=0.05 (5% max drawdown for ultra-conservative)
        - s=1: Y=1.0 (no drawdown limit for ultra-aggressive)
        """
        s = aggressiveness
        if s >= 0.9:
            # No drawdown constraint for very aggressive investors
            return 1.0
        else:
            # Progressive scaling for others
            return 0.05 + 0.50 * (s ** 0.7)
    
    def calculate_sortino_ratio(self, weights: np.ndarray) -> float:
        """
        Calculate Sortino ratio for a portfolio.
        
        Sortino = (Return - Risk_free) / Downside_deviation
        """
        # Portfolio returns
        portfolio_returns = self.returns_data @ weights
        
        # Expected return (annualized)
        expected_return = portfolio_returns.mean() * 12
        
        # Downside deviation (only negative returns)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        if len(downside_returns) > 0:
            downside_deviation = downside_returns.std() * np.sqrt(12)
        else:
            downside_deviation = 0.001  # Small value to avoid division by zero
        
        # Sortino ratio
        sortino = (expected_return - self.risk_free_rate) / downside_deviation
        
        return sortino
    
    def calculate_max_drawdown(self, weights: np.ndarray) -> float:
        """
        Calculate historical maximum drawdown for a portfolio.
        """
        # Portfolio returns
        portfolio_returns = self.returns_data @ weights
        
        # Cumulative returns
        cumulative = (1 + portfolio_returns).cumprod()
        
        # Running maximum
        running_max = cumulative.expanding().max()
        
        # Drawdown
        drawdown = (cumulative - running_max) / running_max
        
        # Maximum drawdown (positive value)
        max_drawdown = abs(drawdown.min())
        
        return max_drawdown
    
    def optimize(self, aggressiveness: float) -> Dict:
        """
        Optimize portfolio for given aggressiveness level.
        
        Args:
            aggressiveness: 0 (ultra-conservative) to 1 (ultra-aggressive)
            
        Returns:
            Dictionary with optimal weights and performance metrics
        """
        n_assets = len(self.returns_data.columns)
        asset_names = self.returns_data.columns.tolist()
        
        # Get constraint parameters
        max_dd_limit = self.calculate_max_drawdown_limit(aggressiveness)
        
        # Objective: blend Sortino ratio with return for aggressive investors
        def objective(weights):
            sortino = self.calculate_sortino_ratio(weights)
            portfolio_returns = self.returns_data @ weights
            expected_return = portfolio_returns.mean() * 12
            
            if aggressiveness >= 0.95:
                # Ultra-aggressive: almost pure return maximization
                return -expected_return
            elif aggressiveness >= 0.8:
                # For aggressive: prioritize return more
                return -(0.2 * sortino + 0.8 * expected_return * 10)
            elif aggressiveness >= 0.5:
                # For moderate: balanced
                return -(0.5 * sortino + 0.5 * expected_return * 10)
            else:
                # For conservative: prioritize Sortino (risk-adjusted)
                return -sortino
        
        # Constraints
        constraints = [
            # Weights sum to 1
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
            
            # Maximum drawdown constraint
            {'type': 'ineq', 'fun': lambda w: max_dd_limit - self.calculate_max_drawdown(w)}
        ]
        
        # Bounds for each asset based on aggressiveness
        bounds = []
        for asset_name in asset_names:
            max_weight = self.calculate_weight_limit(aggressiveness, asset_name)
            bounds.append((0, max_weight))
        
        # Initial guess: equal weights adjusted for bounds
        x0 = np.ones(n_assets) / n_assets
        for i, (lower, upper) in enumerate(bounds):
            x0[i] = min(x0[i], upper)
        x0 = x0 / x0.sum()  # Renormalize
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-9}
        )
        
        if not result.success:
            logger.warning(f"Optimization failed: {result.message}")
            # Fall back to simple weighted allocation
            weights = self._create_fallback_weights(aggressiveness, bounds)
        else:
            weights = result.x
        
        # Calculate performance metrics
        portfolio_returns = self.returns_data @ weights
        annual_return = portfolio_returns.mean() * 12
        annual_vol = portfolio_returns.std() * np.sqrt(12)
        sharpe = (annual_return - self.risk_free_rate) / annual_vol
        sortino = self.calculate_sortino_ratio(weights)
        max_dd = self.calculate_max_drawdown(weights)
        
        # Create weight dictionary
        weight_dict = {asset: w for asset, w in zip(asset_names, weights) if w > 0.001}
        
        return {
            'weights': weight_dict,
            'expected_return': annual_return,
            'volatility': annual_vol,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_dd,
            'aggressiveness': aggressiveness,
            'optimization_success': result.success if 'result' in locals() else False
        }
    
    def _create_fallback_weights(self, aggressiveness: float, bounds: List[Tuple]) -> np.ndarray:
        """Create fallback weights when optimization fails"""
        n_assets = len(bounds)
        asset_names = self.returns_data.columns.tolist()
        
        # Get returns for ranking
        mean_returns = self.returns_data.mean() * 12
        
        # Sort assets by return
        sorted_indices = np.argsort(mean_returns)[::-1]
        
        # Allocate more to top performers for aggressive
        weights = np.zeros(n_assets)
        
        if aggressiveness > 0.7:
            # Aggressive: concentrate in top performers
            for i, idx in enumerate(sorted_indices[:5]):
                weights[idx] = min(0.3, bounds[idx][1])
        elif aggressiveness > 0.3:
            # Moderate: balanced allocation
            for i, idx in enumerate(sorted_indices[:10]):
                weights[idx] = min(0.15, bounds[idx][1])
        else:
            # Conservative: wide diversification
            for i, idx in enumerate(sorted_indices[:15]):
                weights[idx] = min(0.10, bounds[idx][1])
        
        # Normalize
        if weights.sum() > 0:
            weights = weights / weights.sum()
        else:
            weights = np.ones(n_assets) / n_assets
            
        return weights