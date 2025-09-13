"""
Unit tests for ILS Data Manager
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from portfolio.ils_data_manager import ILSDataManager, AssetMetadata


class TestILSDataManager:
    """Test suite for ILS data management and currency conversion"""
    
    @pytest.fixture
    def mock_data_files(self):
        """Mock data files for testing"""
        # Create sample data
        dates = pd.date_range('2020-01-01', periods=24, freq='M')
        
        # Mock exchange rates
        fx_data = pd.DataFrame({
            'Date': dates,
            'Price': np.random.uniform(3.5, 4.0, 24)  # USD/ILS rate
        })
        
        # Mock risk-free rate
        rf_data = pd.DataFrame({
            'Date': dates,
            'Price': np.random.uniform(0.01, 0.03, 24)  # 1-3% annual rate
        })
        
        # Mock asset prices
        asset_data = pd.DataFrame({
            'Date': dates,
            'Price': 100 * (1 + np.random.normal(0.01, 0.05, 24)).cumprod()
        })
        
        return {
            'fx': fx_data,
            'rf': rf_data,
            'asset': asset_data
        }
    
    def test_initialization(self):
        """Test data manager initialization"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            
            assert dm.data_path.exists()
            assert dm.exchange_rates == {}
            assert dm.risk_free_rate is None
            assert dm.raw_assets == {}
            
    def test_asset_metadata_initialization(self):
        """Test asset metadata is properly initialized"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            dm._initialize_asset_metadata()
            
            # Check key assets exist
            assert 'US_Large_Cap_SP500' in dm.asset_metadata
            assert 'Israel_Gov_Indexed_5_10Y' not in dm.asset_metadata  # Not yet added
            
            # Check metadata structure
            sp500 = dm.asset_metadata['US_Large_Cap_SP500']
            assert sp500.category == 'equity'
            assert sp500.region == 'US'
            assert sp500.currency == 'USD'
            
    @patch('pandas.read_csv')
    def test_exchange_rate_loading(self, mock_read_csv, mock_data_files):
        """Test exchange rate data loading"""
        mock_read_csv.return_value = mock_data_files['fx']
        
        with patch('portfolio.ils_data_manager.ILSDataManager._load_risk_free_rate'), \
             patch('portfolio.ils_data_manager.ILSDataManager._load_raw_assets'), \
             patch('portfolio.ils_data_manager.ILSDataManager._process_ils_data'):
            
            dm = ILSDataManager()
            
            # Should load 5 FX pairs
            assert mock_read_csv.call_count >= 5  # USD, EUR, GBP, JPY, INR
            
    @patch('pandas.read_csv')
    def test_risk_free_rate_loading(self, mock_read_csv, mock_data_files):
        """Test risk-free rate loading and conversion"""
        mock_read_csv.return_value = mock_data_files['rf']
        
        with patch('portfolio.ils_data_manager.ILSDataManager._load_exchange_rates'), \
             patch('portfolio.ils_data_manager.ILSDataManager._load_raw_assets'), \
             patch('portfolio.ils_data_manager.ILSDataManager._process_ils_data'):
            
            dm = ILSDataManager()
            dm._load_risk_free_rate()
            
            assert dm.risk_free_rate is not None
            assert len(dm.risk_free_rate) == 24
            assert dm.risk_free_rate.min() >= 0.01
            assert dm.risk_free_rate.max() <= 0.03
            
    def test_currency_conversion_calculation(self):
        """Test currency conversion logic"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            
            # Create sample data
            dates = pd.date_range('2020-01-01', periods=12, freq='M')
            
            # Asset returns in foreign currency
            asset_data = pd.DataFrame({
                'date': dates,
                'return': np.random.normal(0.01, 0.05, 12)
            }).set_index('date')
            
            # FX rates (USD/ILS)
            fx_data = pd.DataFrame({
                'date': dates,
                'fx_rate': [3.5, 3.6, 3.55, 3.7, 3.65, 3.8, 
                           3.75, 3.9, 3.85, 4.0, 3.95, 4.1]
            }).set_index('date')
            
            # Convert to ILS
            ils_returns = dm._convert_asset_to_ils(
                asset_data, fx_data, 'Test_Asset'
            )
            
            assert ils_returns is not None
            assert len(ils_returns) == 11  # First return is NaN
            
    def test_statistics_calculation(self):
        """Test portfolio statistics calculation"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            
            # Create sample returns data
            dates = pd.date_range('2020-01-01', periods=36, freq='M')
            n_assets = 5
            
            dm.returns_data = pd.DataFrame(
                np.random.normal(0.005, 0.02, (36, n_assets)),
                index=dates,
                columns=[f'Asset_{i}' for i in range(n_assets)]
            )
            
            dm.risk_free_rate = pd.Series(
                np.full(36, 0.02),  # 2% annual rate
                index=dates
            )
            
            dm._calculate_statistics()
            
            # Check statistics are calculated
            assert dm.mean_returns is not None
            assert dm.cov_matrix is not None
            assert dm.avg_risk_free_rate is not None
            
            # Check dimensions
            assert len(dm.mean_returns) == n_assets
            assert dm.cov_matrix.shape == (n_assets, n_assets)
            
            # Check annualization
            assert dm.avg_risk_free_rate == pytest.approx(0.02, rel=0.01)
            
    def test_get_asset_indices_by_category(self):
        """Test asset category filtering"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            
            # Setup test data
            dm.returns_data = pd.DataFrame(columns=[
                'US_Large_Cap_SP500',
                'US_Gov_Bonds_3_7Y',
                'Gold_Futures'
            ])
            
            dm._initialize_asset_metadata()
            
            # Test equity indices
            equity_indices = dm.get_asset_indices_by_category('equity')
            assert 0 in equity_indices  # SP500
            assert 1 not in equity_indices  # Bonds
            
            # Test bond indices
            bond_indices = dm.get_asset_indices_by_category('bond')
            assert 1 in bond_indices  # US Gov Bonds
            assert 0 not in bond_indices  # SP500
            
            # Test commodity indices
            commodity_indices = dm.get_asset_indices_by_category('commodity')
            assert 2 in commodity_indices  # Gold
            
    def test_summary_statistics_output(self):
        """Test summary statistics generation"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            
            # Setup minimal test data
            dates = pd.date_range('2020-01-01', periods=24, freq='M')
            dm.returns_data = pd.DataFrame({
                'Test_Asset': np.random.normal(0.01, 0.02, 24)
            }, index=dates)
            
            dm.risk_free_rate = pd.Series(0.02, index=dates)
            dm.avg_risk_free_rate = 0.02
            
            dm.asset_metadata = {
                'Test_Asset': AssetMetadata(
                    'Test_Asset', 'equity', 'US', 'USD', 'Test Asset'
                )
            }
            
            stats = dm.summary_statistics()
            
            assert 'Test_Asset' in stats
            assert 'annual_return' in stats['Test_Asset']
            assert 'annual_volatility' in stats['Test_Asset']
            assert 'sharpe_ratio' in stats['Test_Asset']
            assert stats['Test_Asset']['category'] == 'equity'
            
    def test_monthly_risk_free_conversion(self):
        """Test annual to monthly risk-free rate conversion"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            
            dates = pd.date_range('2020-01-01', periods=12, freq='M')
            dm.returns_data = pd.DataFrame(index=dates)
            
            # Annual rates
            annual_rates = pd.Series([0.01, 0.02, 0.03, 0.04] * 3, index=dates)
            dm.risk_free_rate = annual_rates
            
            # Get monthly rates
            monthly_rates = dm.get_risk_free_rate_series()
            
            # Check conversion: monthly = (1 + annual)^(1/12) - 1
            expected_monthly = (1 + annual_rates)**(1/12) - 1
            
            pd.testing.assert_series_equal(
                monthly_rates, expected_monthly, 
                check_names=False
            )
            
    def test_missing_metadata_handling(self):
        """Test handling of assets without metadata"""
        with patch('portfolio.ils_data_manager.ILSDataManager._load_all_data'):
            dm = ILSDataManager()
            
            # Asset without metadata
            dm.returns_data = pd.DataFrame(columns=['Unknown_Asset'])
            dm.asset_metadata = {}
            
            # Should not crash
            indices = dm.get_asset_indices_by_category('equity')
            assert indices == []
            
            # Summary should handle missing metadata
            dm.returns_data = pd.DataFrame({
                'Unknown_Asset': [0.01, 0.02, 0.03]
            })
            dm.avg_risk_free_rate = 0.02
            
            stats = dm.summary_statistics()
            assert stats['Unknown_Asset']['category'] == 'unknown'