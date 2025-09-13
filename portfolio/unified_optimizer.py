"""
Unified Portfolio Optimizer - Complete Utility-Based Optimization

Implements sophisticated utility maximization with KYC-derived parameters,
CVaR constraints, and multi-objective optimization in ILS terms.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
import time
from datetime import datetime

try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False
    logging.warning("CVXPy not available, using SciPy only")

from .ils_data_manager import ILSDataManager
from kyc.models import KYCResponse

logger = logging.getLogger(__name__)

@dataclass  
class OptimizationParams:
    """Parameters for utility-based optimization"""
    # Utility function parameters
    risk_aversion_lambda: float       # Volatility penalty
    cvar_penalty_alpha: float         # CVaR penalty  
    vol_penalty_beta: float           # Volatility target penalty
    concentration_penalty_gamma: float # Concentration penalty
    skewness_reward_delta: float      # Skewness reward (for aggressive)
    
    # Targets and soft constraints
    target_volatility: float          # Soft volatility target
    target_cvar: float               # Soft CVaR target
    
    # Hard constraints
    max_volatility: float            # Hard volatility limit
    max_cvar: float                  # Hard CVaR limit
    equity_range: Tuple[float, float] # (min, max) equity allocation
    max_single_asset: float          # Maximum single asset weight
    
    # Risk category info
    risk_category: str               # For reporting
    composite_score: float           # Original KYC score

@dataclass
class OptimizationResult:
    """Complete optimization result"""
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
    
    # Metadata
    total_investment_ils: float
    risk_free_rate_used: float
    optimization_success: bool
    optimization_time_ms: float
    risk_category: str
    currency: str = "ILS"

def map_kyc_to_optimization_params(kyc_response: KYCResponse) -> OptimizationParams:
    """Map KYC questionnaire results to optimization parameters"""
    
    # Normalize composite score to [0,1]
    s = kyc_response.composite_score / 100.0
    
    # Extract individual question insights
    loss_tolerance = getattr(kyc_response, 'loss_tolerance', kyc_response.composite_score) / 100.0
    horizon_score = getattr(kyc_response, 'horizon_score', kyc_response.composite_score) / 100.0
    experience_score = getattr(kyc_response, 'experience_score', kyc_response.composite_score) / 100.0
    
    # Calculate utility function parameters
    # Conservative investors heavily penalize risk, aggressive investors barely penalize
    risk_aversion_lambda = 8.0 * (1 - loss_tolerance) + 0.5 * loss_tolerance
    
    # CVaR penalty - influenced by loss tolerance and time horizon
    horizon_factor = max(0.2, horizon_score)  # Don't go below 20%
    cvar_penalty_alpha = 6.0 * (1 - loss_tolerance) * (1 + 0.5 * (1 - horizon_factor))
    
    # Volatility penalty
    vol_penalty_beta = 5.0 * (1 - s) + 1.0 * s
    
    # Concentration penalty - conservative investors want more diversification
    concentration_penalty_gamma = 3.0 * (1 - s) + 0.2 * s
    
    # Skewness reward - only for moderate+ risk tolerance
    skewness_reward_delta = max(0, s - 0.4) * 2.0
    
    # Target levels (soft constraints)
    target_volatility = 0.04 + s * 0.18  # 4% to 22%
    target_cvar = 0.03 + s * 0.12        # 3% to 15% (softer than hard limit)
    
    # Hard constraint limits
    max_volatility = target_volatility + 0.03  # 3% buffer above target
    max_cvar = 0.03 + s * 0.37              # 3% to 40%
    
    # Equity allocation bounds from KYC categories
    if kyc_response.composite_score <= 25:      # Ultra Conservative
        equity_range = (0.05, 0.20)
    elif kyc_response.composite_score <= 45:    # Conservative  
        equity_range = (0.15, 0.40)
    elif kyc_response.composite_score <= 65:    # Moderate
        equity_range = (0.30, 0.65)
    elif kyc_response.composite_score <= 85:    # Aggressive
        equity_range = (0.55, 0.80)
    else:                                      # Very Aggressive
        equity_range = (0.70, 0.95)
    
    # Adjust for time horizon
    if horizon_score < 0.3:  # Short horizon (< 3 years equivalent)
        equity_range = (equity_range[0], min(equity_range[1], 0.5))
        max_cvar = min(max_cvar, 0.08)
    
    # Single asset concentration limit
    max_single_asset = 0.15 + s * 0.25  # 15% to 40%
    
    return OptimizationParams(
        risk_aversion_lambda=risk_aversion_lambda,
        cvar_penalty_alpha=cvar_penalty_alpha,
        vol_penalty_beta=vol_penalty_beta,
        concentration_penalty_gamma=concentration_penalty_gamma,
        skewness_reward_delta=skewness_reward_delta,
        target_volatility=target_volatility,
        target_cvar=target_cvar,
        max_volatility=max_volatility,
        max_cvar=max_cvar,
        equity_range=equity_range,
        max_single_asset=max_single_asset,
        risk_category=kyc_response.category_english,
        composite_score=kyc_response.composite_score
    )

class UnifiedPortfolioOptimizer:
    """Complete utility-based portfolio optimization system"""
    
    def __init__(self, data_manager: Optional[ILSDataManager] = None):
        self.data_manager = data_manager or ILSDataManager()
        self.cache = {}
        
        # Validate data availability
        if self.data_manager.returns_data is None:
            raise ValueError("Data manager not properly initialized")
            
        logger.info(f"Optimizer initialized with {len(self.data_manager.returns_data.columns)} assets")
        
    def optimize_portfolio(self, 
                          kyc_response: KYCResponse,
                          investment_amount: float,
                          investment_duration_years: float = 10.0) -> OptimizationResult:
        """Main optimization entry point"""
        
        start_time = time.time()
        
        # Map KYC to optimization parameters
        params = map_kyc_to_optimization_params(kyc_response)
        
        logger.info(f"Optimizing for {params.risk_category} (score: {params.composite_score:.1f})")
        logger.info(f"Target vol: {params.target_volatility:.1%}, Max CVaR: {params.max_cvar:.1%}")
        logger.info(f"Equity range: {params.equity_range[0]:.1%}-{params.equity_range[1]:.1%}")
        
        # Solve optimization  
        try:
            optimal_weights = self._solve_optimization(params)
            optimization_success = True
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            optimal_weights = self._create_simple_allocation(params)
            optimization_success = False
            
        # Build comprehensive results
        optimization_time = (time.time() - start_time) * 1000
        
        result = self._build_optimization_result(
            optimal_weights, params, investment_amount, 
            optimization_success, optimization_time
        )
        
        logger.info(f"Optimization completed in {optimization_time:.0f}ms")
        logger.info(f"Expected return: {result.expected_return_annual:.1%}, Vol: {result.volatility_annual:.1%}")
        logger.info(f"Sharpe: {result.sharpe_ratio:.2f}, CVaR: {result.cvar_95:.1%}")
        
        return result
        
    def _solve_optimization(self, params: OptimizationParams) -> np.ndarray:
        """Solve the unified optimization problem"""
        
        # Try CVXPy first for convex approximation (if available)
        if CVXPY_AVAILABLE:
            try:
                initial_weights = self._solve_cvxpy_stage(params)
            except Exception as e:
                logger.warning(f"CVXPy stage failed: {e}")
                initial_weights = self._create_equal_weight_start()
        else:
            initial_weights = self._create_equal_weight_start()
            
        # SciPy refinement with full non-convex utility function
        try:
            final_weights = self._solve_scipy_stage(params, initial_weights)
            return final_weights
        except Exception as e:
            logger.warning(f"SciPy stage failed: {e}")
            return initial_weights
            
    def _solve_cvxpy_stage(self, params: OptimizationParams) -> np.ndarray:
        """CVXPy convex approximation stage"""
        
        n_assets = len(self.data_manager.mean_returns)
        w = cp.Variable(n_assets, nonneg=True)
        
        mean_returns = self.data_manager.mean_returns.values
        cov_matrix = self.data_manager.cov_matrix.values
        
        # Portfolio statistics
        portfolio_return = w.T @ mean_returns
        portfolio_var = cp.quad_form(w, cov_matrix)
        portfolio_vol = cp.sqrt(portfolio_var)
        
        # Simplified objective for convexity
        objective = portfolio_return - params.risk_aversion_lambda * portfolio_var
        
        # Basic constraints
        constraints = [
            cp.sum(w) == 1,                    # Fully invested
            portfolio_vol <= params.max_volatility,  # Volatility limit
            w <= params.max_single_asset,     # Concentration limit
        ]
        
        # Equity allocation constraints
        equity_indices = self.data_manager.get_asset_indices_by_category('equity')
        if equity_indices:
            equity_allocation = cp.sum([w[i] for i in equity_indices])
            constraints.extend([
                equity_allocation >= params.equity_range[0],
                equity_allocation <= params.equity_range[1]
            ])
            
        # Bond minimum for conservative portfolios
        if params.composite_score < 50:
            bond_indices = self.data_manager.get_asset_indices_by_category('bond')
            if bond_indices:
                bond_allocation = cp.sum([w[i] for i in bond_indices])
                min_bonds = max(0.1, 0.5 - params.composite_score / 100)
                constraints.append(bond_allocation >= min_bonds)
        
        # Solve
        problem = cp.Problem(cp.Maximize(objective), constraints)
        problem.solve(solver=cp.ECOS, verbose=False)
        
        if problem.status not in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
            raise RuntimeError(f"CVXPy failed: {problem.status}")
            
        return w.value
        
    def _solve_scipy_stage(self, params: OptimizationParams, x0: np.ndarray) -> np.ndarray:
        """SciPy non-convex optimization stage with full utility function"""
        
        def objective_function(w):
            """Complete utility function"""
            
            # Portfolio statistics
            portfolio_return = np.sum(w * self.data_manager.mean_returns.values)
            total_return = portfolio_return + self.data_manager.avg_risk_free_rate
            portfolio_vol = np.sqrt(w.T @ self.data_manager.cov_matrix.values @ w)
            
            # Risk metrics
            cvar = self._calculate_historical_cvar(w)
            concentration_hhi = np.sum(w**2)
            skewness = self._calculate_portfolio_skewness(w)
            
            # Penalty terms
            vol_target_penalty = max(0, portfolio_vol - params.target_volatility)**2
            cvar_target_penalty = max(0, cvar - params.target_cvar)**2
            
            # Complete utility function
            utility = (
                total_return 
                - params.risk_aversion_lambda * portfolio_vol**2
                - params.cvar_penalty_alpha * cvar
                - params.vol_penalty_beta * vol_target_penalty
                - params.concentration_penalty_gamma * concentration_hhi
                + params.skewness_reward_delta * skewness
            )
            
            return -utility  # Minimize negative utility
            
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Fully invested
        ]
        
        # CVaR constraint
        constraints.append({
            'type': 'ineq', 
            'fun': lambda w: params.max_cvar - self._calculate_historical_cvar(w)
        })
        
        # Volatility constraint  
        constraints.append({
            'type': 'ineq',
            'fun': lambda w: params.max_volatility - np.sqrt(w.T @ self.data_manager.cov_matrix.values @ w)
        })
        
        # Equity allocation constraints
        equity_indices = self.data_manager.get_asset_indices_by_category('equity')
        if equity_indices:
            constraints.extend([
                {'type': 'ineq', 'fun': lambda w: np.sum([w[i] for i in equity_indices]) - params.equity_range[0]},
                {'type': 'ineq', 'fun': lambda w: params.equity_range[1] - np.sum([w[i] for i in equity_indices])},
            ])
        
        # Individual asset bounds
        bounds = [(0, params.max_single_asset) for _ in range(len(x0))]
        
        # Optimize
        result = minimize(
            objective_function,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 200, 'ftol': 1e-8}
        )
        
        if not result.success:
            logger.warning(f"SciPy optimization failed: {result.message}")
            
        return result.x
        
    def _calculate_historical_cvar(self, weights: np.ndarray, confidence_level: float = 0.95) -> float:
        """Calculate CVaR using historical simulation"""
        
        # Calculate portfolio returns
        returns_matrix = self.data_manager.returns_data.values
        portfolio_returns = returns_matrix @ weights
        
        # Add risk-free rate to get total returns
        rf_series = self.data_manager.get_risk_free_rate_series().values
        total_returns = portfolio_returns + rf_series
        
        # Annualize returns (assuming monthly data)
        annual_returns = (1 + total_returns)**12 - 1
        
        # Calculate CVaR
        alpha = 1 - confidence_level
        var_threshold = np.percentile(annual_returns, alpha * 100)
        
        tail_losses = annual_returns[annual_returns <= var_threshold]
        cvar = -tail_losses.mean() if len(tail_losses) > 0 else 0
        
        return max(0, cvar)  # Ensure non-negative
        
    def _calculate_portfolio_skewness(self, weights: np.ndarray) -> float:
        """Calculate portfolio skewness"""
        
        portfolio_returns = self.data_manager.returns_data.values @ weights
        
        if len(portfolio_returns) < 3:
            return 0
            
        mean_return = portfolio_returns.mean()
        vol = portfolio_returns.std()
        
        if vol == 0:
            return 0
        
        skewness = ((portfolio_returns - mean_return) ** 3).mean() / (vol ** 3)
        return skewness
        
    def _create_equal_weight_start(self) -> np.ndarray:
        """Create equal-weight starting point"""
        n_assets = len(self.data_manager.mean_returns)
        return np.ones(n_assets) / n_assets
        
    def _create_simple_allocation(self, params: OptimizationParams) -> np.ndarray:
        """Create simple rule-based allocation when optimization fails"""
        
        n_assets = len(self.data_manager.mean_returns)
        weights = np.zeros(n_assets)
        
        # Get asset categories
        equity_indices = self.data_manager.get_asset_indices_by_category('equity')
        bond_indices = self.data_manager.get_asset_indices_by_category('bond')
        other_indices = [i for i in range(n_assets) if i not in equity_indices + bond_indices]
        
        # Target allocations based on risk level
        target_equity = (params.equity_range[0] + params.equity_range[1]) / 2
        target_bonds = min(0.4, 1 - target_equity)
        target_other = max(0, 1 - target_equity - target_bonds)
        
        # Allocate equally within categories
        if equity_indices:
            equity_weight_per_asset = target_equity / len(equity_indices)
            for i in equity_indices:
                weights[i] = equity_weight_per_asset
                
        if bond_indices:
            bond_weight_per_asset = target_bonds / len(bond_indices)  
            for i in bond_indices:
                weights[i] = bond_weight_per_asset
                
        if other_indices and target_other > 0:
            other_weight_per_asset = target_other / len(other_indices)
            for i in other_indices:
                weights[i] = other_weight_per_asset
                
        # Normalize to ensure sum = 1
        weights = weights / weights.sum()
        
        logger.info(f"Created simple allocation: {target_equity:.1%} equity, {target_bonds:.1%} bonds")
        
        return weights
        
    def _build_optimization_result(self,
                                  weights: np.ndarray,
                                  params: OptimizationParams,
                                  investment_amount: float,
                                  optimization_success: bool,
                                  optimization_time_ms: float) -> OptimizationResult:
        """Build comprehensive optimization result"""
        
        # Portfolio metrics
        portfolio_return = np.sum(weights * self.data_manager.mean_returns.values)
        total_expected_return = portfolio_return + self.data_manager.avg_risk_free_rate
        portfolio_vol = np.sqrt(weights.T @ self.data_manager.cov_matrix.values @ weights)
        sharpe_ratio = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
        
        # Risk metrics
        cvar_95 = self._calculate_historical_cvar(weights)
        max_drawdown = self._calculate_max_drawdown(weights)
        concentration_hhi = np.sum(weights**2)
        
        # Create allocation dictionaries
        allocation_pct = {}
        allocation_ils = {}
        risk_contributions = {}
        
        asset_names = self.data_manager.get_asset_names()
        
        for i, asset_name in enumerate(asset_names):
            if weights[i] > 0.005:  # Include assets with >0.5% allocation
                allocation_pct[asset_name] = round(weights[i], 4)
                allocation_ils[asset_name] = round(investment_amount * weights[i], 2)
                
                # Risk contribution (marginal * weight)
                marginal_contrib = (self.data_manager.cov_matrix.values @ weights)[i] 
                risk_contributions[asset_name] = weights[i] * marginal_contrib / (portfolio_vol**2)
        
        return OptimizationResult(
            allocation_percentages=allocation_pct,
            allocation_ils_amounts=allocation_ils,
            expected_return_annual=total_expected_return,
            volatility_annual=portfolio_vol,
            sharpe_ratio=sharpe_ratio,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            risk_contributions=risk_contributions,
            concentration_hhi=concentration_hhi,
            total_investment_ils=investment_amount,
            risk_free_rate_used=self.data_manager.avg_risk_free_rate,
            optimization_success=optimization_success,
            optimization_time_ms=optimization_time_ms,
            risk_category=params.risk_category
        )
        
    def _calculate_max_drawdown(self, weights: np.ndarray) -> float:
        """Calculate maximum drawdown using historical data"""
        
        portfolio_returns = self.data_manager.returns_data.values @ weights
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns / running_max) - 1
        
        return drawdown.min()  # Most negative value