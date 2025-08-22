"""
Advanced Portfolio Analytics Module

Provides sophisticated analysis capabilities for portfolio optimization,
including performance attribution, risk analysis, and market event detection.
Designed to support future momentum strategies and real-time market analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import stats
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for a portfolio or asset"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    value_at_risk_95: float
    conditional_var_95: float
    skewness: float
    kurtosis: float
    winning_periods: float
    avg_win: float
    avg_loss: float


@dataclass
class MarketRegime:
    """Market regime classification for advanced analysis"""
    regime_type: str  # 'bull', 'bear', 'sideways', 'volatile'
    start_date: datetime
    end_date: datetime
    return_characteristics: Dict[str, float]
    volatility_level: str  # 'low', 'medium', 'high'


class PortfolioAnalytics:
    """
    Advanced analytics engine for portfolio analysis.
    Supports sophisticated metrics and prepares for momentum strategies.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def calculate_comprehensive_metrics(self, 
                                      returns: pd.Series,
                                      benchmark_returns: Optional[pd.Series] = None) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics for a return series.
        
        Args:
            returns: Daily returns series
            benchmark_returns: Optional benchmark for relative metrics
        """
        returns = returns.dropna()
        
        if len(returns) < 30:
            raise ValueError("Insufficient data for meaningful metrics calculation")
        
        # Basic metrics
        total_return = (1 + returns).prod() - 1
        periods_per_year = 252  # Assuming daily returns
        annualized_return = (1 + total_return) ** (periods_per_year / len(returns)) - 1
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        # Risk-adjusted metrics
        excess_returns = returns - self.risk_free_rate / periods_per_year
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(periods_per_year)
        
        # Downside deviation for Sortino ratio
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(periods_per_year)
        sortino_ratio = (annualized_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        
        # Drawdown analysis
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Value at Risk and Conditional VaR
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()
        
        # Distribution characteristics
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        # Win/loss analysis
        winning_periods = (returns > 0).sum() / len(returns)
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            value_at_risk_95=var_95,
            conditional_var_95=cvar_95,
            skewness=skewness,
            kurtosis=kurtosis,
            winning_periods=winning_periods,
            avg_win=avg_win,
            avg_loss=avg_loss
        )
    
    def detect_market_regimes(self, 
                            returns: pd.Series,
                            window: int = 60) -> List[MarketRegime]:
        """
        Detect market regimes for advanced portfolio management.
        Future: Enhance for momentum strategy signals.
        
        Args:
            returns: Return series with datetime index
            window: Rolling window for regime detection
        """
        regimes = []
        
        if len(returns) < window * 2:
            return regimes
        
        # Calculate rolling metrics
        rolling_returns = returns.rolling(window).mean()
        rolling_vol = returns.rolling(window).std()
        
        # Define regime thresholds
        vol_low = rolling_vol.quantile(0.33)
        vol_high = rolling_vol.quantile(0.67)
        return_threshold = 0.0
        
        current_regime = None
        regime_start = None
        
        for date, ret_mean in rolling_returns.dropna().items():
            vol = rolling_vol.loc[date]
            
            # Classify regime
            if ret_mean > return_threshold:
                if vol < vol_low:
                    regime_type = 'bull_low_vol'
                elif vol > vol_high:
                    regime_type = 'bull_high_vol'
                else:
                    regime_type = 'bull'
            else:
                if vol < vol_low:
                    regime_type = 'bear_low_vol'
                elif vol > vol_high:
                    regime_type = 'bear_high_vol'
                else:
                    regime_type = 'bear'
            
            # Track regime changes
            if current_regime != regime_type:
                if current_regime is not None:
                    # End previous regime
                    end_date = date
                    regime_returns = returns[regime_start:end_date]
                    
                    regimes.append(MarketRegime(
                        regime_type=current_regime,
                        start_date=regime_start,
                        end_date=end_date,
                        return_characteristics={
                            'mean_return': regime_returns.mean(),
                            'volatility': regime_returns.std(),
                            'duration_days': len(regime_returns)
                        },
                        volatility_level='high' if vol > vol_high else 'low' if vol < vol_low else 'medium'
                    ))
                
                current_regime = regime_type
                regime_start = date
        
        return regimes
    
    def calculate_portfolio_attribution(self,
                                      portfolio_returns: pd.Series,
                                      asset_returns: pd.DataFrame,
                                      weights: pd.Series) -> Dict[str, float]:
        """
        Calculate performance attribution by asset.
        
        Args:
            portfolio_returns: Portfolio return series
            asset_returns: Asset returns DataFrame
            weights: Portfolio weights
        """
        # Align data
        common_dates = portfolio_returns.index.intersection(asset_returns.index)
        portfolio_returns = portfolio_returns.loc[common_dates]
        asset_returns = asset_returns.loc[common_dates]
        
        # Calculate contributions
        contributions = {}
        for asset in asset_returns.columns:
            if asset in weights.index:
                asset_contribution = (asset_returns[asset] * weights[asset]).sum()
                contributions[asset] = asset_contribution
        
        return contributions
    
    def analyze_correlation_structure(self, 
                                    returns_df: pd.DataFrame,
                                    window: int = 60) -> Dict[str, any]:
        """
        Analyze correlation structure for risk management.
        Future: Enhance for regime-dependent correlations.
        """
        # Static correlation matrix
        correlation_matrix = returns_df.corr()
        
        # Rolling correlations (average)
        rolling_corrs = []
        for i in range(window, len(returns_df)):
            window_data = returns_df.iloc[i-window:i]
            rolling_corrs.append(window_data.corr())
        
        # Average correlation levels
        avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix, k=1)].mean()
        max_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix, k=1)].max()
        
        # Correlation stability (how much correlations change over time)
        if rolling_corrs:
            correlation_changes = []
            for i in range(1, len(rolling_corrs)):
                diff = np.abs(rolling_corrs[i].values - rolling_corrs[i-1].values)
                correlation_changes.append(np.nanmean(diff[np.triu_indices_from(diff, k=1)]))
            
            correlation_stability = 1 - np.mean(correlation_changes)
        else:
            correlation_stability = 1.0
        
        return {
            'correlation_matrix': correlation_matrix,
            'average_correlation': avg_correlation,
            'max_correlation': max_correlation,
            'correlation_stability': correlation_stability,
            'highly_correlated_pairs': self._find_high_correlation_pairs(correlation_matrix, threshold=0.7)
        }
    
    def _find_high_correlation_pairs(self, 
                                   correlation_matrix: pd.DataFrame,
                                   threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """Find pairs of assets with high correlation"""
        high_corr_pairs = []
        
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                asset1 = correlation_matrix.columns[i]
                asset2 = correlation_matrix.columns[j]
                corr = correlation_matrix.iloc[i, j]
                
                if abs(corr) > threshold:
                    high_corr_pairs.append((asset1, asset2, corr))
        
        return sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True)
    
    def calculate_risk_contributions(self,
                                   weights: np.ndarray,
                                   cov_matrix: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate marginal and component risk contributions.
        Essential for risk budgeting and advanced portfolio construction.
        """
        weights = np.array(weights)
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix.values, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Marginal contributions
        marginal_contrib = np.dot(cov_matrix.values, weights) / portfolio_volatility
        
        # Component contributions
        component_contrib = weights * marginal_contrib
        
        # Percentage contributions
        pct_contrib = component_contrib / portfolio_volatility
        
        results = {}
        for i, asset in enumerate(cov_matrix.columns):
            results[asset] = {
                'marginal_contribution': marginal_contrib[i],
                'component_contribution': component_contrib[i],
                'percentage_contribution': pct_contrib[i]
            }
        
        return results
    
    def stress_test_portfolio(self,
                            weights: np.ndarray,
                            asset_returns: pd.DataFrame,
                            scenarios: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Stress test portfolio under various scenarios.
        
        Args:
            weights: Portfolio weights
            asset_returns: Historical asset returns
            scenarios: Dict of scenario_name -> {asset_name: shock_percentage}
        """
        results = {}
        
        for scenario_name, shocks in scenarios.items():
            # Apply shocks to returns
            shocked_returns = asset_returns.copy()
            for asset, shock in shocks.items():
                if asset in shocked_returns.columns:
                    shocked_returns[asset] = shocked_returns[asset] + shock
            
            # Calculate portfolio returns under stress
            portfolio_returns = (shocked_returns * weights).sum(axis=1)
            portfolio_metrics = self.calculate_comprehensive_metrics(portfolio_returns)
            
            results[scenario_name] = {
                'total_return': portfolio_metrics.total_return,
                'max_drawdown': portfolio_metrics.max_drawdown,
                'volatility': portfolio_metrics.volatility,
                'var_95': portfolio_metrics.value_at_risk_95
            }
        
        return results
    
    def identify_similar_market_periods(self,
                                      current_returns: pd.Series,
                                      historical_returns: pd.Series,
                                      window: int = 30,
                                      similarity_threshold: float = 0.8) -> List[Dict[str, any]]:
        """
        Identify historical periods similar to current market conditions.
        Future: Enhance for real-time market event analysis.
        
        Args:
            current_returns: Recent return series
            historical_returns: Full historical return series
            window: Comparison window size
            similarity_threshold: Correlation threshold for similarity
        """
        similar_periods = []
        
        if len(current_returns) < window:
            return similar_periods
        
        # Use the most recent window of current returns
        recent_pattern = current_returns.tail(window)
        
        # Compare with all historical windows
        for i in range(window, len(historical_returns) - window):
            historical_window = historical_returns.iloc[i-window:i]
            
            # Calculate similarity (correlation)
            correlation = recent_pattern.corr(historical_window)
            
            if correlation > similarity_threshold:
                # Analyze what happened next in historical data
                future_window = historical_returns.iloc[i:i+window]
                future_return = (1 + future_window).prod() - 1
                future_volatility = future_window.std() * np.sqrt(252)
                future_max_dd = self._calculate_max_drawdown(future_window)
                
                similar_periods.append({
                    'start_date': historical_returns.index[i-window],
                    'end_date': historical_returns.index[i-1],
                    'similarity_score': correlation,
                    'subsequent_return': future_return,
                    'subsequent_volatility': future_volatility,
                    'subsequent_max_drawdown': future_max_dd
                })
        
        return sorted(similar_periods, key=lambda x: x['similarity_score'], reverse=True)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Helper to calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return drawdown.min()