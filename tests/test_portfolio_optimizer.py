"""
Unit tests for Unified Portfolio Optimizer
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from portfolio.unified_optimizer import (
    UnifiedPortfolioOptimizer,
    OptimizationParams,
    OptimizationResult,
    map_kyc_to_optimization_params
)
from kyc.models import KYCResponse


class TestOptimizationParamsMapping:
    """Test KYC to optimization parameters mapping"""
    
    def test_ultra_conservative_mapping(self):
        """Test parameter mapping for ultra conservative profile"""
        kyc_response = Mock(spec=KYCResponse)
        kyc_response.composite_score = 10
        kyc_response.loss_tolerance = 0
        kyc_response.horizon_score = 20
        kyc_response.experience_score = 10
        kyc_response.category_english = "Ultra Conservative"
        
        params = map_kyc_to_optimization_params(kyc_response)
        
        assert params.risk_aversion_lambda > 7  # High risk aversion
        assert params.cvar_penalty_alpha > 5    # High CVaR penalty
        assert params.target_volatility < 0.08  # Low volatility target
        assert params.max_cvar < 0.10          # Low CVaR limit
        assert params.equity_range == (0.05, 0.20)  # Low equity
        
    def test_moderate_mapping(self):
        """Test parameter mapping for moderate profile"""
        kyc_response = Mock(spec=KYCResponse)
        kyc_response.composite_score = 55
        kyc_response.loss_tolerance = 60
        kyc_response.horizon_score = 50
        kyc_response.experience_score = 60
        kyc_response.category_english = "Moderate"
        
        params = map_kyc_to_optimization_params(kyc_response)
        
        assert 2 < params.risk_aversion_lambda < 5
        assert params.target_volatility > 0.10
        assert params.target_volatility < 0.16
        assert params.equity_range == (0.30, 0.65)
        
    def test_aggressive_mapping(self):
        """Test parameter mapping for aggressive profile"""
        kyc_response = Mock(spec=KYCResponse)
        kyc_response.composite_score = 90
        kyc_response.loss_tolerance = 100
        kyc_response.horizon_score = 100
        kyc_response.experience_score = 90
        kyc_response.category_english = "Very Aggressive"
        
        params = map_kyc_to_optimization_params(kyc_response)
        
        assert params.risk_aversion_lambda < 1.5  # Low risk aversion
        assert params.target_volatility > 0.18    # High volatility tolerance
        assert params.max_cvar > 0.30            # High CVaR tolerance
        assert params.equity_range == (0.70, 0.95)  # High equity
        assert params.skewness_reward_delta > 0   # Reward skewness
        
    def test_short_horizon_adjustment(self):
        """Test that short horizon reduces equity allocation"""
        kyc_response = Mock(spec=KYCResponse)
        kyc_response.composite_score = 70
        kyc_response.loss_tolerance = 70
        kyc_response.horizon_score = 10  # Very short horizon
        kyc_response.experience_score = 70
        kyc_response.category_english = "Aggressive"
        
        params = map_kyc_to_optimization_params(kyc_response)
        
        # Short horizon should cap equity
        assert params.equity_range[1] <= 0.50
        assert params.max_cvar <= 0.08


class TestUnifiedPortfolioOptimizer:
    """Test suite for portfolio optimization engine"""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create mock data manager"""
        dm = Mock()
        
        # Create sample data
        n_assets = 10
        n_periods = 60
        
        dates = pd.date_range('2020-01-01', periods=n_periods, freq='M')
        returns = pd.DataFrame(
            np.random.normal(0.005, 0.02, (n_periods, n_assets)),
            index=dates,
            columns=[f'Asset_{i}' for i in range(n_assets)]
        )
        
        dm.returns_data = returns
        dm.mean_returns = pd.Series(
            np.random.uniform(-0.05, 0.15, n_assets),
            index=returns.columns
        )
        dm.cov_matrix = returns.cov()
        dm.avg_risk_free_rate = 0.02
        
        # Asset metadata
        dm.asset_metadata = {
            f'Asset_{i}': Mock(
                category='equity' if i < 6 else 'bond',
                region='US',
                currency='USD'
            ) for i in range(n_assets)
        }
        
        def get_indices(category):
            if category == 'equity':
                return list(range(6))
            elif category == 'bond':
                return list(range(6, 10))
            return []
        
        dm.get_asset_indices_by_category = get_indices
        dm.get_asset_names = lambda: list(returns.columns)
        dm.get_risk_free_rate_series = lambda: pd.Series(0.02/12, index=dates)
        
        return dm
    
    @pytest.fixture
    def optimizer(self, mock_data_manager):
        """Create optimizer with mock data"""
        with patch('portfolio.unified_optimizer.ILSDataManager', return_value=mock_data_manager):
            return UnifiedPortfolioOptimizer(mock_data_manager)
    
    @pytest.fixture
    def conservative_kyc(self):
        """Conservative KYC response"""
        kyc = Mock(spec=KYCResponse)
        kyc.composite_score = 30
        kyc.loss_tolerance = 20
        kyc.horizon_score = 50
        kyc.experience_score = 30
        kyc.category_english = "Conservative"
        kyc.category_hebrew = "שמרני"
        kyc.risk_level = 3
        kyc.inconsistencies = []
        return kyc
    
    def test_optimizer_initialization(self, mock_data_manager):
        """Test optimizer initialization"""
        with patch('portfolio.unified_optimizer.ILSDataManager', return_value=mock_data_manager):
            opt = UnifiedPortfolioOptimizer()
            
            assert opt.data_manager is not None
            assert opt.cache == {}
            
    def test_portfolio_optimization_conservative(self, optimizer, conservative_kyc):
        """Test conservative portfolio optimization"""
        result = optimizer.optimize_portfolio(
            conservative_kyc,
            investment_amount=100000,
            investment_duration_years=10
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_success is True
        assert result.total_investment_ils == 100000
        assert result.risk_category == "Conservative"
        
        # Check allocations sum to 100%
        total_allocation = sum(result.allocation_percentages.values())
        assert abs(total_allocation - 1.0) < 0.01
        
        # Check ILS amounts match percentages
        for asset, pct in result.allocation_percentages.items():
            expected_amount = 100000 * pct
            actual_amount = result.allocation_ils_amounts[asset]
            assert abs(actual_amount - expected_amount) < 1
            
    def test_cvar_calculation(self, optimizer):
        """Test CVaR calculation"""
        weights = np.array([0.5, 0.5] + [0] * 8)  # 50/50 on first two assets
        
        cvar = optimizer._calculate_historical_cvar(weights)
        
        assert isinstance(cvar, float)
        assert cvar >= 0  # CVaR should be non-negative (loss)
        
    def test_portfolio_skewness_calculation(self, optimizer):
        """Test portfolio skewness calculation"""
        weights = np.array([1] + [0] * 9)  # 100% in first asset
        
        skewness = optimizer._calculate_portfolio_skewness(weights)
        
        assert isinstance(skewness, float)
        assert -10 < skewness < 10  # Reasonable range
        
    def test_max_drawdown_calculation(self, optimizer):
        """Test maximum drawdown calculation"""
        weights = np.array([0.1] * 10)  # Equal weight
        
        max_dd = optimizer._calculate_max_drawdown(weights)
        
        assert isinstance(max_dd, float)
        assert max_dd <= 0  # Drawdown should be negative
        assert max_dd > -1  # Should not exceed -100%
        
    def test_constraint_satisfaction(self, optimizer, conservative_kyc):
        """Test that optimization respects constraints"""
        params = map_kyc_to_optimization_params(conservative_kyc)
        
        # Mock optimization to return specific weights
        test_weights = np.array([0.3, 0.3, 0.2, 0.1, 0.1] + [0] * 5)
        
        with patch.object(optimizer, '_solve_optimization', return_value=test_weights):
            result = optimizer.optimize_portfolio(
                conservative_kyc,
                investment_amount=100000,
                investment_duration_years=10
            )
            
            # Check equity allocation is within bounds
            equity_allocation = sum(
                result.allocation_percentages.get(f'Asset_{i}', 0) 
                for i in range(6)  # First 6 are equity
            )
            
            assert params.equity_range[0] <= equity_allocation <= params.equity_range[1]
            
    def test_optimization_failure_handling(self, optimizer, conservative_kyc):
        """Test handling of optimization failure"""
        # Force optimization to fail
        with patch.object(optimizer, '_solve_scipy_stage', side_effect=Exception("Optimization failed")):
            result = optimizer.optimize_portfolio(
                conservative_kyc,
                investment_amount=100000,
                investment_duration_years=10
            )
            
            # Should still return a result with simple allocation
            assert isinstance(result, OptimizationResult)
            assert result.optimization_success is False
            assert len(result.allocation_percentages) > 0
            
    def test_category_breakdown(self, optimizer, conservative_kyc):
        """Test category breakdown in results"""
        result = optimizer.optimize_portfolio(
            conservative_kyc,
            investment_amount=100000,
            investment_duration_years=10
        )
        
        # Should have risk contributions
        assert isinstance(result.risk_contributions, dict)
        
        # Check concentration metric
        assert 0 <= result.concentration_hhi <= 1
        
    def test_performance_metrics(self, optimizer, conservative_kyc):
        """Test portfolio performance metrics"""
        result = optimizer.optimize_portfolio(
            conservative_kyc,
            investment_amount=100000,
            investment_duration_years=10
        )
        
        # Check all metrics are present and reasonable
        assert -0.5 < result.expected_return_annual < 0.5  # -50% to 50%
        assert 0 < result.volatility_annual < 1.0  # 0% to 100%
        assert -5 < result.sharpe_ratio < 5
        assert 0 <= result.cvar_95 < 1.0  # 0% to 100%
        assert -1.0 <= result.max_drawdown <= 0
        
    def test_optimization_timing(self, optimizer, conservative_kyc):
        """Test that optimization completes in reasonable time"""
        result = optimizer.optimize_portfolio(
            conservative_kyc,
            investment_amount=100000,
            investment_duration_years=10
        )
        
        # Should complete within 5 seconds
        assert result.optimization_time_ms < 5000
        assert result.optimization_time_ms > 0