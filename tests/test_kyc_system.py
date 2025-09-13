"""
Unit tests for KYC risk assessment system
"""

import pytest
from kyc.risk_assessor import KYCRiskAssessor
from kyc.models import KYCResponse, RiskProfile, InconsistencyType


class TestKYCRiskAssessor:
    """Test suite for KYC risk assessment functionality"""
    
    @pytest.fixture
    def assessor(self):
        """Create a KYC risk assessor instance"""
        return KYCRiskAssessor()
    
    @pytest.fixture
    def ultra_conservative_responses(self):
        """Ultra conservative investor profile"""
        return {
            "horizon_score": 10,
            "loss_tolerance": 0,
            "experience_score": 20,
            "financial_score": 20,
            "goal_score": 0,
            "sleep_score": 0
        }
    
    @pytest.fixture
    def moderate_responses(self):
        """Moderate investor profile"""
        return {
            "horizon_score": 50,
            "loss_tolerance": 60,
            "experience_score": 70,
            "financial_score": 50,
            "goal_score": 60,
            "sleep_score": 30
        }
    
    @pytest.fixture
    def aggressive_responses(self):
        """Aggressive investor profile"""
        return {
            "horizon_score": 100,
            "loss_tolerance": 100,
            "experience_score": 100,
            "financial_score": 100,
            "goal_score": 100,
            "sleep_score": 100
        }
    
    def test_ultra_conservative_assessment(self, assessor, ultra_conservative_responses):
        """Test ultra conservative risk profile assessment"""
        result = assessor.process_responses(ultra_conservative_responses)
        
        assert isinstance(result, RiskProfile)
        assert result.category_hebrew == 'שמרני_מאוד'
        assert result.category_english == 'Ultra Conservative'
        assert result.composite_score < 25
        assert result.risk_level <= 3
        assert result.max_drawdown == 0.03
        assert result.target_volatility == 0.04
        
    def test_moderate_assessment(self, assessor, moderate_responses):
        """Test moderate risk profile assessment"""
        result = assessor.process_responses(moderate_responses)
        
        assert isinstance(result, RiskProfile)
        assert result.category_hebrew == 'מתון'
        assert result.category_english == 'Moderate'
        assert 46 <= result.composite_score <= 65
        assert 5 <= result.risk_level <= 7
        assert result.max_drawdown == 0.15
        assert result.target_volatility == 0.12
        
    def test_aggressive_assessment(self, assessor, aggressive_responses):
        """Test aggressive risk profile assessment"""
        result = assessor.process_responses(aggressive_responses)
        
        assert isinstance(result, RiskProfile)
        assert result.category_hebrew == 'אגרסיבי_מאוד'
        assert result.category_english == 'Very Aggressive'
        assert result.composite_score > 85
        assert result.risk_level >= 9
        assert result.max_drawdown == 0.40
        assert result.target_volatility == 0.22
        
    def test_inconsistency_detection_short_horizon_high_risk(self, assessor):
        """Test detection of short horizon with high risk tolerance"""
        responses = {
            "horizon_score": 10,  # Very short term
            "loss_tolerance": 90,  # Very high risk tolerance
            "experience_score": 50,
            "financial_score": 50,
            "goal_score": 50,
            "sleep_score": 50
        }
        
        result = assessor.process_responses(responses)
        
        assert len(result.inconsistencies) > 0
        assert any(inc.type == InconsistencyType.SHORT_HORIZON_HIGH_RISK 
                  for inc in result.inconsistencies)
        
    def test_inconsistency_detection_low_capacity_high_appetite(self, assessor):
        """Test detection of low financial capacity with high risk appetite"""
        responses = {
            "horizon_score": 50,
            "loss_tolerance": 80,  # High risk appetite
            "experience_score": 50,
            "financial_score": 20,  # Low financial capacity
            "goal_score": 80,
            "sleep_score": 50
        }
        
        result = assessor.process_responses(responses)
        
        assert len(result.inconsistencies) > 0
        assert any(inc.type == InconsistencyType.LOW_CAPACITY_HIGH_APPETITE 
                  for inc in result.inconsistencies)
        assert any(inc.severity == 'error' for inc in result.inconsistencies)
        
    def test_missing_fields_validation(self, assessor):
        """Test validation of missing required fields"""
        incomplete_responses = {
            "horizon_score": 50,
            "loss_tolerance": 50
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            assessor.process_responses(incomplete_responses)
            
    def test_invalid_score_ranges(self, assessor):
        """Test validation of score ranges"""
        invalid_responses = {
            "horizon_score": 150,  # Invalid: > 100
            "loss_tolerance": -10,  # Invalid: < 0
            "experience_score": 50,
            "financial_score": 50,
            "goal_score": 50,
            "sleep_score": 50
        }
        
        with pytest.raises(ValueError):
            assessor.process_responses(invalid_responses)
            
    def test_composite_score_calculation(self, assessor):
        """Test composite score calculation with weights"""
        responses = {
            "horizon_score": 100,  # Weight: 0.25
            "loss_tolerance": 80,  # Weight: 0.30
            "experience_score": 60,  # Weight: 0.20
            "financial_score": 40,  # Weight: 0.15
            "goal_score": 20,  # Weight: 0.10
            "sleep_score": 50  # Not used in scoring
        }
        
        result = assessor.process_responses(responses)
        
        # Expected: 100*0.25 + 80*0.30 + 60*0.20 + 40*0.15 + 20*0.10 = 69
        assert 68 <= result.composite_score <= 70
        
    def test_equity_range_by_category(self, assessor):
        """Test equity allocation ranges for different risk categories"""
        test_cases = [
            (10, (0.05, 0.20)),  # Ultra Conservative
            (35, (0.15, 0.40)),  # Conservative
            (55, (0.30, 0.65)),  # Moderate
            (75, (0.55, 0.80)),  # Aggressive
            (95, (0.70, 0.95))   # Very Aggressive
        ]
        
        for score, expected_range in test_cases:
            responses = {
                "horizon_score": score,
                "loss_tolerance": score,
                "experience_score": score,
                "financial_score": score,
                "goal_score": score,
                "sleep_score": score
            }
            
            result = assessor.process_responses(responses)
            assert result.equity_range == expected_range
            
    def test_consistency_adjustments(self, assessor):
        """Test that inconsistencies trigger score adjustments"""
        # Create responses that should trigger adjustments
        responses = {
            "horizon_score": 20,  # Short term
            "loss_tolerance": 80,  # High risk (inconsistent)
            "experience_score": 20,  # Low experience
            "financial_score": 80,
            "goal_score": 80,
            "sleep_score": 20  # Low sleep tolerance (inconsistent with loss tolerance)
        }
        
        result = assessor.process_responses(responses)
        
        # Should have inconsistencies
        assert len(result.inconsistencies) > 0
        
        # Adjusted score should be more conservative
        assert result.composite_score < 70