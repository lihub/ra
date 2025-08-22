"""
Data Management Module for Portfolio Optimization

Handles efficient loading, caching, and processing of financial data.
Designed for extensibility to support advanced features like momentum strategies.
"""

import pandas as pd
import numpy as np
import pickle
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class AssetMetadata:
    """Metadata for each asset"""
    name: str
    category: str  # 'equity', 'bond', 'currency', 'commodity', 'alternative'
    region: str    # 'us', 'international', 'emerging', 'global'
    currency: str  # 'USD', 'EUR', 'ILS', etc.
    risk_level: int  # 1-5 scale for asset-level risk classification


class MarketDataManager:
    """
    Centralized manager for all market data operations.
    Supports caching, advanced analytics, and extensibility for momentum strategies.
    """
    
    def __init__(self, 
                 processed_data_path: str = "processed_data",
                 cache_path: str = "cache",
                 cache_expiry_hours: int = 24):
        self.processed_data_path = Path(processed_data_path)
        self.cache_path = Path(cache_path)
        self.cache_expiry_hours = cache_expiry_hours
        
        # Ensure cache directory exists
        self.cache_path.mkdir(exist_ok=True)
        
        # Asset metadata mapping
        self.asset_metadata = self._initialize_asset_metadata()
        
        # In-memory cache for frequently accessed data
        self._memory_cache = {}
        self._cache_timestamps = {}
    
    def _initialize_asset_metadata(self) -> Dict[str, AssetMetadata]:
        """Initialize metadata for all available assets"""
        metadata = {
            # US Equity
            'US_Large_Cap_SP500': AssetMetadata('S&P 500', 'equity', 'us', 'USD', 3),
            'US_Small_Cap_Russell2000': AssetMetadata('Russell 2000', 'equity', 'us', 'USD', 4),
            'NASDAQ_Total_Return': AssetMetadata('NASDAQ', 'equity', 'us', 'USD', 4),
            
            # International Equity
            'Europe_MSCI': AssetMetadata('MSCI Europe', 'equity', 'international', 'EUR', 3),
            'Japan_MSCI': AssetMetadata('MSCI Japan', 'equity', 'international', 'JPY', 3),
            'Emerging_Markets_MSCI': AssetMetadata('MSCI EM', 'equity', 'emerging', 'USD', 4),
            'Germany_DAX': AssetMetadata('DAX', 'equity', 'international', 'EUR', 3),
            'France_CAC40': AssetMetadata('CAC 40', 'equity', 'international', 'EUR', 3),
            'UK_FTSE100': AssetMetadata('FTSE 100', 'equity', 'international', 'GBP', 3),
            'India_NIFTY': AssetMetadata('NIFTY', 'equity', 'emerging', 'INR', 4),
            
            # Israeli Markets
            'Israel_TA125': AssetMetadata('TA-125', 'equity', 'international', 'ILS', 4),
            'Israel_SME60': AssetMetadata('SME 60', 'equity', 'international', 'ILS', 5),
            
            # Bonds
            'US_Gov_Bonds_3_7Y': AssetMetadata('US Treasury 3-7Y', 'bond', 'us', 'USD', 2),
            'US_Gov_Bonds_Short': AssetMetadata('US Treasury Short', 'bond', 'us', 'USD', 1),
            'Israel_Gov_Indexed_0_2Y': AssetMetadata('IL Gov Indexed 0-2Y', 'bond', 'international', 'ILS', 1),
            'Israel_Gov_Indexed_5_10Y': AssetMetadata('IL Gov Indexed 5-10Y', 'bond', 'international', 'ILS', 2),
            'Israel_Gov_Shekel_0_2Y': AssetMetadata('IL Gov Shekel 0-2Y', 'bond', 'international', 'ILS', 1),
            'Israel_Gov_Shekel_5_10Y': AssetMetadata('IL Gov Shekel 5-10Y', 'bond', 'international', 'ILS', 2),
            'Israel_TelBond_60': AssetMetadata('TelBond 60', 'bond', 'international', 'ILS', 2),
            'Israel_TelBond_Shekel': AssetMetadata('TelBond Shekel', 'bond', 'international', 'ILS', 2),
            
            # Currencies
            'USD_ILS_FX': AssetMetadata('USD/ILS', 'currency', 'global', 'ILS', 2),
            'EUR_ILS_FX': AssetMetadata('EUR/ILS', 'currency', 'global', 'ILS', 2),
            'GBP_ILS_FX': AssetMetadata('GBP/ILS', 'currency', 'global', 'ILS', 2),
            'JPY_ILS_FX': AssetMetadata('JPY/ILS', 'currency', 'global', 'ILS', 2),
            'INR_ILS_FX': AssetMetadata('INR/ILS', 'currency', 'global', 'ILS', 3),
            
            # Commodities
            'Gold_Futures': AssetMetadata('Gold', 'commodity', 'global', 'USD', 3),
            'Oil_Brent_Futures': AssetMetadata('Brent Oil', 'commodity', 'global', 'USD', 5),
        }
        return metadata
    
    def get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for given operation and parameters"""
        import hashlib
        key_parts = [operation]
        for k, v in sorted(kwargs.items()):
            # Convert list to string for hashing
            if isinstance(v, list):
                v = str(sorted(v))
            key_parts.append(f"{k}_{v}")
        
        full_key = "_".join(key_parts)
        
        # If key is too long for Windows filesystem, use hash
        if len(full_key) > 200:
            hash_key = hashlib.md5(full_key.encode()).hexdigest()
            return f"{operation}_{hash_key}"
        
        return full_key
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_file.exists():
            return False
        
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(hours=self.cache_expiry_hours)
        return file_time > expiry_time
    
    def _save_to_cache(self, data: any, cache_key: str) -> None:
        """Save data to disk cache"""
        cache_file = self.cache_path / f"{cache_key}.pkl"
        try:
            joblib.dump(data, cache_file, compress=3)
            logger.info(f"Saved cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {e}")
    
    def _load_from_cache(self, cache_key: str) -> Optional[any]:
        """Load data from disk cache"""
        cache_file = self.cache_path / f"{cache_key}.pkl"
        
        if self._is_cache_valid(cache_file):
            try:
                data = joblib.load(cache_file)
                logger.info(f"Loaded from cache: {cache_key}")
                return data
            except Exception as e:
                logger.warning(f"Failed to load cache {cache_key}: {e}")
        
        return None
    
    def load_asset_data(self, asset_name: str) -> Optional[pd.DataFrame]:
        """Load data for a single asset with caching"""
        cache_key = f"asset_data_{asset_name}"
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            if (datetime.now() - self._cache_timestamps[cache_key]).total_seconds() < 3600:  # 1 hour
                return self._memory_cache[cache_key].copy()
        
        # Check disk cache
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            self._memory_cache[cache_key] = cached_data
            self._cache_timestamps[cache_key] = datetime.now()
            return cached_data.copy()
        
        # Load from CSV
        csv_file = self.processed_data_path / f"clean_{asset_name}.csv"
        if not csv_file.exists():
            logger.warning(f"Asset data file not found: {csv_file}")
            return None
        
        try:
            df = pd.read_csv(csv_file)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
            
            # Cache the data
            self._memory_cache[cache_key] = df
            self._cache_timestamps[cache_key] = datetime.now()
            self._save_to_cache(df, cache_key)
            
            return df.copy()
            
        except Exception as e:
            logger.error(f"Error loading asset data {asset_name}: {e}")
            return None
    
    def load_all_assets(self, asset_filter: Optional[Dict[str, any]] = None) -> Dict[str, pd.DataFrame]:
        """
        Load all available assets with optional filtering.
        
        Args:
            asset_filter: Dict with keys like 'category', 'region', 'risk_level' for filtering
        """
        cache_key = self.get_cache_key("all_assets", **(asset_filter or {}))
        
        # Check cache
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        asset_data = {}
        
        for asset_name, metadata in self.asset_metadata.items():
            # Apply filters
            if asset_filter:
                if 'category' in asset_filter and metadata.category != asset_filter['category']:
                    continue
                if 'region' in asset_filter and metadata.region != asset_filter['region']:
                    continue
                if 'risk_level' in asset_filter and metadata.risk_level != asset_filter['risk_level']:
                    continue
                if 'max_risk_level' in asset_filter and metadata.risk_level > asset_filter['max_risk_level']:
                    continue
            
            data = self.load_asset_data(asset_name)
            if data is not None and len(data) > 100:  # Minimum data requirement
                asset_data[asset_name] = data
        
        # Cache the result
        self._save_to_cache(asset_data, cache_key)
        
        return asset_data
    
    def calculate_returns_matrix(self, 
                                asset_data: Dict[str, pd.DataFrame],
                                return_type: str = 'daily') -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        """
        Calculate aligned returns matrix, mean returns, and covariance matrix.
        
        Args:
            asset_data: Dict of asset name -> DataFrame
            return_type: 'daily', 'weekly', 'monthly'
        
        Returns:
            (returns_df, mean_returns, cov_matrix)
        """
        cache_key = self.get_cache_key("returns_matrix", 
                                       assets=sorted(asset_data.keys()),
                                       return_type=return_type)
        
        # Check cache
        cached_result = self._load_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Calculate returns for each asset
        asset_returns = {}
        for asset_name, data in asset_data.items():
            data = data.copy()
            data['Returns'] = data['Price'].pct_change()
            
            # Resample if needed
            if return_type == 'weekly':
                data = data.set_index('Date').resample('W').last()
                data['Returns'] = data['Price'].pct_change()
            elif return_type == 'monthly':
                data = data.set_index('Date').resample('M').last()
                data['Returns'] = data['Price'].pct_change()
            
            asset_returns[asset_name] = data[['Date' if 'Date' in data.columns else data.index, 'Returns']].dropna()
        
        # Find common date range
        common_dates = None
        for asset_name, data in asset_returns.items():
            dates = set(data['Date'] if 'Date' in data.columns else data.index)
            if common_dates is None:
                common_dates = dates
            else:
                common_dates = common_dates.intersection(dates)
        
        common_dates = sorted(list(common_dates))
        
        if len(common_dates) < 100:
            raise ValueError(f"Insufficient common dates: {len(common_dates)}")
        
        # Create aligned returns matrix
        returns_matrix = []
        asset_names = []
        
        for asset_name, data in asset_returns.items():
            if 'Date' in data.columns:
                data_dict = dict(zip(data['Date'], data['Returns']))
            else:
                data_dict = dict(zip(data.index, data['Returns']))
            
            aligned_returns = []
            for date in common_dates:
                if date in data_dict and not pd.isna(data_dict[date]):
                    aligned_returns.append(data_dict[date])
                else:
                    aligned_returns.append(0.0)  # Fill missing with 0
            
            returns_matrix.append(aligned_returns)
            asset_names.append(asset_name)
        
        returns_df = pd.DataFrame(np.array(returns_matrix).T, 
                                 columns=asset_names,
                                 index=common_dates)
        
        # Calculate annualized statistics
        periods_per_year = {'daily': 252, 'weekly': 52, 'monthly': 12}[return_type]
        
        mean_returns = returns_df.mean() * periods_per_year
        cov_matrix = returns_df.cov() * periods_per_year
        
        result = (returns_df, mean_returns, cov_matrix)
        
        # Cache the result
        self._save_to_cache(result, cache_key)
        
        return result
    
    def get_asset_categories(self) -> Dict[str, List[str]]:
        """Get assets grouped by category"""
        categories = {}
        for asset_name, metadata in self.asset_metadata.items():
            if metadata.category not in categories:
                categories[metadata.category] = []
            categories[metadata.category].append(asset_name)
        return categories
    
    def get_available_assets(self) -> List[str]:
        """Get list of all available assets"""
        return list(self.asset_metadata.keys())
    
    def validate_data_quality(self, asset_name: str) -> Dict[str, any]:
        """
        Validate data quality for an asset.
        Future: Extend for advanced market event detection.
        """
        data = self.load_asset_data(asset_name)
        if data is None:
            return {'valid': False, 'reason': 'No data available'}
        
        # Basic quality checks
        price_col = 'Price'
        if price_col not in data.columns:
            return {'valid': False, 'reason': 'No price column'}
        
        # Check for sufficient data
        if len(data) < 100:
            return {'valid': False, 'reason': 'Insufficient data points'}
        
        # Check for extreme outliers (potential data errors)
        returns = data[price_col].pct_change().dropna()
        extreme_threshold = 0.3  # 30% daily change threshold
        extreme_days = (abs(returns) > extreme_threshold).sum()
        
        # Check for long gaps
        date_diffs = data['Date'].diff().dt.days
        max_gap = date_diffs.max()
        
        return {
            'valid': True,
            'data_points': len(data),
            'date_range': (data['Date'].min(), data['Date'].max()),
            'extreme_days': extreme_days,
            'max_gap_days': max_gap,
            'mean_daily_return': returns.mean(),
            'volatility': returns.std()
        }
    
    def clear_cache(self, cache_type: str = 'all') -> None:
        """Clear cache (memory and/or disk)"""
        if cache_type in ['memory', 'all']:
            self._memory_cache.clear()
            self._cache_timestamps.clear()
            
        if cache_type in ['disk', 'all']:
            for cache_file in self.cache_path.glob("*.pkl"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")