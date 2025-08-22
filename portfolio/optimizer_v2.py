"""
Enhanced Portfolio Optimizer with Duration Support

Modern portfolio optimization engine with support for investment horizons,
advanced risk metrics, and extensibility for momentum strategies.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from .data_manager import MarketDataManager, AssetMetadata
from .analytics import PortfolioAnalytics, PerformanceMetrics

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConstraints:
    """Configuration for portfolio optimization constraints"""
    max_single_asset: float = 0.4
    min_single_asset: float = 0.0
    max_category_allocation: Dict[str, float] = None
    min_category_allocation: Dict[str, float] = None
    max_volatility: Optional[float] = None
    min_expected_return: Optional[float] = None
    max_correlation_exposure: float = 0.8  # Max exposure to highly correlated assets
    
    def __post_init__(self):
        if self.max_category_allocation is None:
            self.max_category_allocation = {}
        if self.min_category_allocation is None:
            self.min_category_allocation = {}


@dataclass
class OptimizationResult:
    """Comprehensive optimization result"""
    allocation: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    risk_contributions: Dict[str, Dict[str, float]]
    performance_metrics: PerformanceMetrics
    optimization_success: bool
    constraints_satisfied: bool
    performance_history: Dict[str, any]
    asset_metadata: Dict[str, AssetMetadata]


class AdvancedPortfolioOptimizer:
    """
    Advanced portfolio optimizer with duration support and extensibility.
    Designed for current needs and future momentum strategies.
    """
    
    def __init__(self, 
                 data_manager: Optional[MarketDataManager] = None,
                 analytics: Optional[PortfolioAnalytics] = None,
                 risk_free_rate: float = 0.02):
        
        self.data_manager = data_manager or MarketDataManager()
        self.analytics = analytics or PortfolioAnalytics(risk_free_rate)
        self.risk_free_rate = risk_free_rate
        
        # Cache for optimization data
        self._current_assets = None
        self._current_returns_df = None
        self._current_mean_returns = None
        self._current_cov_matrix = None
        
    def _get_duration_adjusted_constraints(self, 
                                         risk_level: int,
                                         investment_duration_years: float) -> OptimizationConstraints:
        """
        Generate duration-adjusted constraints based on risk level and time horizon.
        
        Key insight: Longer horizons allow for more equity exposure and risk-taking.
        """
        constraints = OptimizationConstraints()
        
        # Base constraints from risk level
        if risk_level <= 3:  # Conservative
            constraints.max_single_asset = 0.35
            base_equity_max = 0.6
            constraints.min_category_allocation = {'bond': 0.25}
        elif risk_level <= 7:  # Moderate
            constraints.max_single_asset = 0.4
            base_equity_max = 0.8
            constraints.min_category_allocation = {'bond': 0.1}
        else:  # Aggressive
            constraints.max_single_asset = 0.5
            base_equity_max = 0.95
            constraints.min_category_allocation = {}
        
        # Duration adjustments
        # Longer duration = can handle more volatility and equity exposure
        duration_factor = min(investment_duration_years / 10.0, 1.5)  # Cap at 1.5x for 10+ years
        
        # Adjust equity allocation based on duration
        adjusted_equity_max = min(base_equity_max * duration_factor, 0.95)
        constraints.max_category_allocation = {'equity': adjusted_equity_max}
        
        # Adjust volatility tolerance
        base_vol_tolerance = 0.08 + (risk_level - 1) * (0.25 - 0.08) / 9
        constraints.max_volatility = base_vol_tolerance * (1 + duration_factor * 0.3)
        
        # For very short durations (< 2 years), be more conservative
        if investment_duration_years < 2:
            constraints.max_category_allocation['equity'] = min(adjusted_equity_max, 0.5)
            constraints.min_category_allocation['bond'] = max(
                constraints.min_category_allocation.get('bond', 0), 0.3
            )
        
        return constraints
    
    def _filter_assets_by_duration(self, 
                                 all_assets: Dict[str, pd.DataFrame],
                                 investment_duration_years: float) -> Dict[str, pd.DataFrame]:
        """
        Filter and weight assets based on investment duration.
        Some assets are better suited for different time horizons.
        """
        filtered_assets = {}
        
        for asset_name, data in all_assets.items():
            metadata = self.data_manager.asset_metadata.get(asset_name)
            if not metadata:
                continue
            
            include_asset = True
            
            # Duration-based filtering logic
            if investment_duration_years < 2:
                # Short duration: prefer bonds and stable assets
                if metadata.category == 'commodity' and metadata.risk_level > 3:
                    include_asset = False  # Skip volatile commodities
                elif metadata.category == 'equity' and metadata.risk_level > 4:
                    include_asset = False  # Skip very risky equities
            
            elif investment_duration_years > 15:
                # Long duration: can handle more volatile assets
                if metadata.category == 'bond' and 'Short' in metadata.name:
                    continue  # Skip short-term bonds for long horizons
            
            if include_asset:
                filtered_assets[asset_name] = data
        
        return filtered_assets
    
    def _calculate_duration_adjusted_returns(self,
                                           mean_returns: pd.Series,
                                           investment_duration_years: float) -> pd.Series:
        """
        Adjust expected returns based on investment duration.
        Shorter durations may prefer more stable, lower-return assets.
        """
        adjusted_returns = mean_returns.copy()
        
        # For shorter durations, slightly penalize very volatile assets
        if investment_duration_years < 3:
            for asset_name in adjusted_returns.index:
                metadata = self.data_manager.asset_metadata.get(asset_name)
                if metadata and metadata.risk_level >= 4:
                    # Slight return penalty for high-risk assets in short horizons
                    adjusted_returns[asset_name] *= (0.9 + investment_duration_years * 0.05)
        
        return adjusted_returns
    
    def optimize_portfolio(self,
                          risk_level: int = 5,
                          investment_duration_years: float = 10.0,
                          investment_amount: float = 10000.0,
                          custom_constraints: Optional[OptimizationConstraints] = None,
                          asset_filter: Optional[Dict[str, any]] = None) -> OptimizationResult:
        """
        Optimize portfolio with duration support and advanced constraints.
        
        Args:
            risk_level: 1-10 scale (1=very conservative, 10=very aggressive)
            investment_duration_years: Investment time horizon in years
            investment_amount: Portfolio value for calculations
            custom_constraints: Override default constraints
            asset_filter: Filter assets by category, region, etc.
        """
        logger.info(f"Starting optimization: risk_level={risk_level}, duration={investment_duration_years}y")
        
        # Load and filter assets
        all_assets = self.data_manager.load_all_assets(asset_filter)
        filtered_assets = self._filter_assets_by_duration(all_assets, investment_duration_years)
        
        if len(filtered_assets) < 2:
            raise ValueError("Insufficient assets available for optimization")
        
        # Calculate returns matrix
        returns_df, mean_returns, cov_matrix = self.data_manager.calculate_returns_matrix(filtered_assets)
        
        # Store for later use
        self._current_assets = filtered_assets
        self._current_returns_df = returns_df
        self._current_mean_returns = mean_returns
        self._current_cov_matrix = cov_matrix
        
        # Apply duration adjustments to expected returns
        duration_adjusted_returns = self._calculate_duration_adjusted_returns(
            mean_returns, investment_duration_years
        )
        
        # Get constraints
        constraints = custom_constraints or self._get_duration_adjusted_constraints(
            risk_level, investment_duration_years
        )
        
        # Perform optimization
        optimal_weights = self._optimize_weights(
            duration_adjusted_returns, cov_matrix, constraints
        )
        
        # Calculate portfolio metrics
        portfolio_return = np.sum(duration_adjusted_returns * optimal_weights)
        portfolio_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        # Create allocation dictionary
        allocation = {}
        asset_metadata = {}
        for i, asset_name in enumerate(duration_adjusted_returns.index):
            if optimal_weights[i] > 0.005:  # Include assets with >0.5% allocation
                allocation[asset_name] = round(optimal_weights[i], 4)
                asset_metadata[asset_name] = self.data_manager.asset_metadata.get(asset_name)
        
        # Calculate risk contributions
        risk_contributions = self.analytics.calculate_risk_contributions(
            optimal_weights, cov_matrix
        )
        
        # Generate performance history
        portfolio_returns = (returns_df * optimal_weights).sum(axis=1)
        performance_metrics = self.analytics.calculate_comprehensive_metrics(portfolio_returns)
        performance_history = self._generate_performance_history(
            portfolio_returns, investment_amount
        )
        
        # Check constraint satisfaction
        constraints_satisfied = self._validate_constraints(optimal_weights, allocation, constraints)
        
        return OptimizationResult(
            allocation=allocation,
            expected_return=round(portfolio_return, 4),
            volatility=round(portfolio_vol, 4),
            sharpe_ratio=round(sharpe_ratio, 4),
            risk_contributions=risk_contributions,
            performance_metrics=performance_metrics,
            optimization_success=True,
            constraints_satisfied=constraints_satisfied,
            performance_history=performance_history,
            asset_metadata=asset_metadata
        )
    
    def _optimize_weights(self,
                         expected_returns: pd.Series,
                         cov_matrix: pd.DataFrame,
                         constraints: OptimizationConstraints) -> np.ndarray:
        """
        Core optimization engine using scipy.optimize.
        """
        n_assets = len(expected_returns)
        
        def objective(weights):
            """Maximize Sharpe ratio (minimize negative Sharpe)"""
            portfolio_return = np.sum(expected_returns * weights)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(portfolio_return - self.risk_free_rate) / portfolio_vol
        
        # Constraints
        optimization_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]
        
        # Volatility constraint
        if constraints.max_volatility:
            def vol_constraint(weights):
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                return constraints.max_volatility - portfolio_vol
            optimization_constraints.append({'type': 'ineq', 'fun': vol_constraint})
        
        # Return constraint
        if constraints.min_expected_return:
            def return_constraint(weights):
                portfolio_return = np.sum(expected_returns * weights)
                return portfolio_return - constraints.min_expected_return
            optimization_constraints.append({'type': 'ineq', 'fun': return_constraint})
        
        # Category constraints
        asset_categories = {}
        for i, asset_name in enumerate(expected_returns.index):
            metadata = self.data_manager.asset_metadata.get(asset_name)
            if metadata:
                category = metadata.category
                if category not in asset_categories:
                    asset_categories[category] = []
                asset_categories[category].append(i)
        
        # Add category constraints
        for category, max_allocation in constraints.max_category_allocation.items():
            if category in asset_categories:
                indices = asset_categories[category]
                def category_max_constraint(weights, indices=indices, max_alloc=max_allocation):
                    return max_alloc - np.sum([weights[i] for i in indices])
                optimization_constraints.append({'type': 'ineq', 'fun': category_max_constraint})
        
        for category, min_allocation in constraints.min_category_allocation.items():
            if category in asset_categories:
                indices = asset_categories[category]
                def category_min_constraint(weights, indices=indices, min_alloc=min_allocation):
                    return np.sum([weights[i] for i in indices]) - min_alloc
                optimization_constraints.append({'type': 'ineq', 'fun': category_min_constraint})
        
        # Bounds for individual assets
        bounds = tuple((constraints.min_single_asset, constraints.max_single_asset) 
                      for _ in range(n_assets))
        
        # Initial guess - equal weights with slight bias towards bonds for conservative portfolios
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=optimization_constraints,
            options={'maxiter': 1000, 'ftol': 1e-9}
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
            # Fallback to equal weights
            return np.ones(n_assets) / n_assets
        
        return result.x
    
    def _validate_constraints(self,
                            weights: np.ndarray,
                            allocation: Dict[str, float],
                            constraints: OptimizationConstraints) -> bool:
        """Validate that optimization result satisfies constraints"""
        
        # Check individual asset limits
        for weight in weights:
            if weight > constraints.max_single_asset + 1e-6:  # Small tolerance
                return False
            if weight < constraints.min_single_asset - 1e-6:
                return False
        
        # Check category constraints
        category_allocations = {}
        for asset_name, weight in allocation.items():
            metadata = self.data_manager.asset_metadata.get(asset_name)
            if metadata:
                category = metadata.category
                category_allocations[category] = category_allocations.get(category, 0) + weight
        
        for category, max_alloc in constraints.max_category_allocation.items():
            if category_allocations.get(category, 0) > max_alloc + 1e-6:
                return False
        
        for category, min_alloc in constraints.min_category_allocation.items():
            if category_allocations.get(category, 0) < min_alloc - 1e-6:
                return False
        
        return True
    
    def _generate_performance_history(self,
                                    portfolio_returns: pd.Series,
                                    initial_value: float = 10000) -> Dict[str, any]:
        """Generate historical performance data for visualization"""
        
        # Calculate cumulative performance
        cumulative_returns = (1 + portfolio_returns).cumprod()
        portfolio_values = initial_value * cumulative_returns
        
        # Sample data for chart (weekly)
        if len(portfolio_values) > 500:
            sample_indices = range(0, len(portfolio_values), 7)
            sampled_values = portfolio_values.iloc[sample_indices]
            sampled_dates = portfolio_returns.index[sample_indices]
        else:
            sampled_values = portfolio_values
            sampled_dates = portfolio_returns.index
        
        # Create timeseries data
        timeseries = []
        for date, value in zip(sampled_dates, sampled_values):
            timeseries.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(value, 2),
                'pnl': round(value - initial_value, 2),
                'pnl_percent': round((value - initial_value) / initial_value * 100, 2)
            })
        
        # Summary statistics
        final_value = portfolio_values.iloc[-1]
        total_return = (final_value - initial_value) / initial_value
        max_value = portfolio_values.max()
        min_value = portfolio_values.min()
        
        # Calculate drawdown
        rolling_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        return {
            'timeseries': timeseries,
            'summary': {
                'initial_value': initial_value,
                'final_value': round(final_value, 2),
                'total_return_percent': round(total_return * 100, 2),
                'max_value': round(max_value, 2),
                'min_value': round(min_value, 2),
                'max_drawdown_percent': round(max_drawdown * 100, 2)
            }
        }
    
    def get_optimization_insights(self,
                                result: OptimizationResult,
                                investment_duration_years: float) -> Dict[str, any]:
        """
        Generate insights and explanations for the optimization result.
        Helps users understand the portfolio construction logic.
        """
        insights = {
            'duration_impact': self._analyze_duration_impact(result, investment_duration_years),
            'risk_analysis': self._analyze_risk_profile(result),
            'diversification_analysis': self._analyze_diversification(result),
            'recommendations': self._generate_recommendations(result, investment_duration_years)
        }
        
        return insights
    
    def _analyze_duration_impact(self, result: OptimizationResult, duration: float) -> Dict[str, any]:
        """Analyze how investment duration affected the portfolio"""
        equity_allocation = sum(
            weight for asset, weight in result.allocation.items()
            if result.asset_metadata.get(asset, AssetMetadata('', 'unknown', '', '', 0)).category == 'equity'
        )
        
        bond_allocation = sum(
            weight for asset, weight in result.allocation.items()
            if result.asset_metadata.get(asset, AssetMetadata('', 'unknown', '', '', 0)).category == 'bond'
        )
        
        if duration < 3:
            duration_category = 'short'
        elif duration < 10:
            duration_category = 'medium'
        else:
            duration_category = 'long'
        
        return {
            'duration_category': duration_category,
            'equity_allocation': equity_allocation,
            'bond_allocation': bond_allocation,
            'explanation': self._get_duration_explanation(duration_category, equity_allocation)
        }
    
    def _get_duration_explanation(self, duration_category: str, equity_allocation: float) -> str:
        """Generate explanation for duration-based allocation"""
        if duration_category == 'short':
            return f"Short-term focus: {equity_allocation:.1%} equity allocation provides growth while managing volatility for your {duration_category} horizon."
        elif duration_category == 'medium':
            return f"Balanced approach: {equity_allocation:.1%} equity allocation balances growth potential with stability for your {duration_category} investment horizon."
        else:
            return f"Long-term growth: {equity_allocation:.1%} equity allocation maximizes growth potential given your {duration_category} investment horizon."
    
    def _analyze_risk_profile(self, result: OptimizationResult) -> Dict[str, any]:
        """Analyze the risk characteristics of the portfolio"""
        risk_level = 'low' if result.volatility < 0.12 else 'medium' if result.volatility < 0.20 else 'high'
        
        return {
            'risk_level': risk_level,
            'volatility': result.volatility,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.performance_metrics.max_drawdown,
            'risk_explanation': f"Portfolio volatility of {result.volatility:.1%} indicates {risk_level} risk level."
        }
    
    def _analyze_diversification(self, result: OptimizationResult) -> Dict[str, any]:
        """Analyze diversification characteristics"""
        category_allocation = {}
        region_allocation = {}
        
        for asset, weight in result.allocation.items():
            metadata = result.asset_metadata.get(asset)
            if metadata:
                category_allocation[metadata.category] = category_allocation.get(metadata.category, 0) + weight
                region_allocation[metadata.region] = region_allocation.get(metadata.region, 0) + weight
        
        diversification_score = len(result.allocation) / 10.0  # Simple metric
        
        return {
            'diversification_score': min(diversification_score, 1.0),
            'category_allocation': category_allocation,
            'region_allocation': region_allocation,
            'number_of_assets': len(result.allocation)
        }
    
    def _generate_recommendations(self, result: OptimizationResult, duration: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if result.sharpe_ratio < 0.5:
            recommendations.append("Consider reviewing risk tolerance - current allocation may be too conservative.")
        
        if len(result.allocation) < 5:
            recommendations.append("Portfolio could benefit from additional diversification across asset classes.")
        
        if duration > 10 and sum(w for a, w in result.allocation.items() 
                                if result.asset_metadata.get(a, AssetMetadata('', 'bond', '', '', 0)).category == 'bond') > 0.4:
            recommendations.append("Long investment horizon allows for higher equity allocation for better growth potential.")
        
        return recommendations