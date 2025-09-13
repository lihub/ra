"""
Integration tests for FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json


class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
    def test_homepage(self, client):
        """Test homepage rendering"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
    def test_language_switching(self, client):
        """Test language preference setting"""
        response = client.get("/set-language?lang=he&redirect_to=/")
        
        assert response.status_code == 200
        assert "language" in response.cookies
        
    @patch('main.KYCRiskAssessor')
    @patch('main.UnifiedPortfolioOptimizer')
    def test_portfolio_calculation_success(self, mock_optimizer_class, mock_assessor_class, client):
        """Test successful portfolio calculation"""
        
        # Mock KYC assessment
        mock_assessor = Mock()
        mock_risk_profile = Mock()
        mock_risk_profile.category_english = "Moderate"
        mock_risk_profile.category_hebrew = "מתון"
        mock_risk_profile.composite_score = 55.0
        mock_risk_profile.risk_level = 6
        mock_risk_profile.inconsistencies = []
        mock_risk_profile.has_warnings = Mock(return_value=False)
        mock_assessor.process_responses.return_value = mock_risk_profile
        mock_assessor_class.return_value = mock_assessor
        
        # Mock portfolio optimization
        mock_optimizer = Mock()
        mock_result = Mock()
        mock_result.allocation_percentages = {
            'US_Large_Cap_SP500': 0.30,
            'US_Gov_Bonds_3_7Y': 0.40,
            'Gold_Futures': 0.30
        }
        mock_result.allocation_ils_amounts = {
            'US_Large_Cap_SP500': 30000,
            'US_Gov_Bonds_3_7Y': 40000,
            'Gold_Futures': 30000
        }
        mock_result.expected_return_annual = 0.08
        mock_result.volatility_annual = 0.12
        mock_result.sharpe_ratio = 0.5
        mock_result.cvar_95 = 0.15
        mock_result.max_drawdown = -0.20
        mock_result.risk_free_rate_used = 0.02
        mock_result.concentration_hhi = 0.34
        mock_result.risk_contributions = {
            'US_Large_Cap_SP500': 0.35,
            'US_Gov_Bonds_3_7Y': 0.30,
            'Gold_Futures': 0.35
        }
        mock_result.optimization_success = True
        mock_result.optimization_time_ms = 450.5
        mock_result.risk_category = "Moderate"
        mock_result.total_investment_ils = 100000
        mock_result.currency = "ILS"
        
        mock_optimizer.optimize_portfolio.return_value = mock_result
        mock_optimizer.data_manager = Mock()
        mock_optimizer.data_manager.asset_metadata = {
            'US_Large_Cap_SP500': Mock(category='equity'),
            'US_Gov_Bonds_3_7Y': Mock(category='bond'),
            'Gold_Futures': Mock(category='commodity')
        }
        mock_optimizer_class.return_value = mock_optimizer
        
        # Test request
        request_data = {
            "responses": {
                "horizon_score": 50,
                "loss_tolerance": 60,
                "experience_score": 70,
                "financial_score": 50,
                "goal_score": 60,
                "sleep_score": 30
            },
            "investment_amount": 100000,
            "investment_duration": 10
        }
        
        response = client.post("/api/calculate-portfolio", json=request_data)
        
        assert response.status_code == 200
        
        result = response.json()
        
        # Check response structure
        assert "risk_assessment" in result
        assert "portfolio_allocation" in result
        assert "performance_metrics" in result
        assert "optimization_info" in result
        
        # Check risk assessment
        assert result["risk_assessment"]["category"] == "Moderate"
        assert result["risk_assessment"]["composite_score"] == 55.0
        assert result["risk_assessment"]["risk_level"] == 6
        
        # Check portfolio allocation
        assert len(result["portfolio_allocation"]["percentages"]) == 3
        assert result["portfolio_allocation"]["total_invested"] == 100000
        
        # Check performance metrics
        assert result["performance_metrics"]["expected_return_annual"] == 8.0
        assert result["performance_metrics"]["volatility_annual"] == 12.0
        assert result["performance_metrics"]["sharpe_ratio"] == 0.5
        
        # Check optimization info
        assert result["optimization_info"]["success"] is True
        assert result["optimization_info"]["risk_category"] == "Moderate"
        
    def test_portfolio_calculation_missing_fields(self, client):
        """Test portfolio calculation with missing required fields"""
        
        # Missing required fields
        request_data = {
            "responses": {
                "horizon_score": 50,
                "loss_tolerance": 60
                # Missing other required fields
            },
            "investment_amount": 100000,
            "investment_duration": 10
        }
        
        response = client.post("/api/calculate-portfolio", json=request_data)
        
        # Should return error
        assert response.status_code == 400 or response.status_code == 422
        
    def test_portfolio_calculation_invalid_values(self, client):
        """Test portfolio calculation with invalid values"""
        
        request_data = {
            "responses": {
                "horizon_score": 150,  # Invalid: > 100
                "loss_tolerance": -10,  # Invalid: < 0
                "experience_score": 50,
                "financial_score": 50,
                "goal_score": 50,
                "sleep_score": 50
            },
            "investment_amount": 100000,
            "investment_duration": 10
        }
        
        response = client.post("/api/calculate-portfolio", json=request_data)
        
        # Should return error
        assert response.status_code == 400 or response.status_code == 422
        
    @patch('main.KYCRiskAssessor')
    def test_portfolio_calculation_with_inconsistencies(self, mock_assessor_class, client):
        """Test portfolio calculation with KYC inconsistencies"""
        
        # Mock KYC with warnings
        mock_assessor = Mock()
        mock_risk_profile = Mock()
        mock_risk_profile.category_english = "Conservative"
        mock_risk_profile.category_hebrew = "שמרני"
        mock_risk_profile.composite_score = 35.0
        mock_risk_profile.risk_level = 3
        
        # Add inconsistency
        mock_inconsistency = Mock()
        mock_inconsistency.type = Mock(value="SHORT_HORIZON_HIGH_RISK")
        mock_inconsistency.message_english = "Short horizon with high risk"
        mock_inconsistency.severity = "warning"
        mock_risk_profile.inconsistencies = [mock_inconsistency]
        mock_risk_profile.has_warnings = Mock(return_value=True)
        
        mock_assessor.process_responses.return_value = mock_risk_profile
        mock_assessor_class.return_value = mock_assessor
        
        request_data = {
            "responses": {
                "horizon_score": 10,  # Short
                "loss_tolerance": 90,  # High risk
                "experience_score": 50,
                "financial_score": 50,
                "goal_score": 50,
                "sleep_score": 50
            },
            "investment_amount": 100000,
            "investment_duration": 10
        }
        
        with patch('main.UnifiedPortfolioOptimizer'):
            response = client.post("/api/calculate-portfolio", json=request_data)
        
        result = response.json()
        
        # Should include inconsistencies
        assert "kyc_inconsistencies" in result
        assert len(result["kyc_inconsistencies"]) == 1
        assert result["kyc_inconsistencies"][0]["type"] == "SHORT_HORIZON_HIGH_RISK"
        
    def test_content_reload_endpoint(self, client):
        """Test content reload endpoint"""
        with patch('main.content_loader.reload_content'):
            response = client.get("/reload-content")
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            
    def test_static_files_serving(self, client):
        """Test that static files are properly mounted"""
        # This would fail in test environment without actual static files
        # Just checking the mount exists
        from main import app
        
        # Check static files are mounted
        routes = [route.path for route in app.routes]
        assert any('/static' in route for route in routes)