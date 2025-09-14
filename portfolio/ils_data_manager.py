"""
ILS Data Manager - Currency Conversion and Data Processing

Handles loading all asset data, converting to ILS using exchange rates,
and preparing unified returns matrix for portfolio optimization.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AssetMetadata:
    """Metadata for each asset"""
    name: str
    category: str  # 'equity', 'bond', 'commodity', 'currency', 'reit'
    region: str    # 'US', 'Europe', 'Asia', 'Israel', 'Global'
    currency: str  # Original currency
    description: str

class ILSDataManager:
    """Manages all market data conversion to ILS terms"""
    
    def __init__(self, data_path: str = "processed_data"):
        self.data_path = Path(data_path)
        self.exchange_rates = {}
        self.risk_free_rate = None
        self.raw_assets = {}
        self.asset_metadata = {}
        self.returns_data = None
        self.mean_returns = None
        self.cov_matrix = None
        self.avg_risk_free_rate = None
        
        self._initialize_asset_metadata()
        self._load_all_data()
        
    def _initialize_asset_metadata(self):
        """Define metadata for all assets"""
        self.asset_metadata = {
            # US Equity
            'US_Large_Cap_SP500': AssetMetadata(
                'US_Large_Cap_SP500', 'equity', 'US', 'USD', 
                'S&P 500 Total Return - Large Cap US Stocks'
            ),
            'NASDAQ_Total_Return': AssetMetadata(
                'NASDAQ_Total_Return', 'equity', 'US', 'USD',
                'NASDAQ Composite Total Return - Tech Heavy'
            ),
            'US_Small_Cap_Russell2000': AssetMetadata(
                'US_Small_Cap_Russell2000', 'equity', 'US', 'USD',
                'Russell 2000 - US Small Cap Stocks'
            ),
            'US_REIT_Select': AssetMetadata(
                'US_REIT_Select', 'reit', 'US', 'USD',
                'Dow Jones US Select REIT - Real Estate'
            ),
            
            # US Bonds
            'US_Gov_Bonds_3_7Y': AssetMetadata(
                'US_Gov_Bonds_3_7Y', 'bond', 'US', 'USD',
                'US Treasury 3-7 Year Bonds'
            ),
            'US_Gov_Bonds_Short': AssetMetadata(
                'US_Gov_Bonds_Short', 'bond', 'US', 'USD',
                'US Treasury Short Term Bonds'
            ),
            
            # International Equity
            'Europe_MSCI': AssetMetadata(
                'Europe_MSCI', 'equity', 'Europe', 'EUR',
                'MSCI Europe Index'
            ),
            'Germany_DAX': AssetMetadata(
                'Germany_DAX', 'equity', 'Europe', 'EUR',
                'German DAX Index'
            ),
            'France_CAC40': AssetMetadata(
                'France_CAC40', 'equity', 'Europe', 'EUR',
                'French CAC 40 Index'
            ),
            'UK_FTSE100': AssetMetadata(
                'UK_FTSE100', 'equity', 'Europe', 'GBP',
                'UK FTSE 100 Index'
            ),
            'Japan_MSCI': AssetMetadata(
                'Japan_MSCI', 'equity', 'Asia', 'JPY',
                'MSCI Japan Index'
            ),
            'India_NIFTY': AssetMetadata(
                'India_NIFTY', 'equity', 'Asia', 'INR',
                'Indian NIFTY 50 Index'
            ),
            'Emerging_Markets_MSCI': AssetMetadata(
                'Emerging_Markets_MSCI', 'equity', 'Global', 'USD',
                'MSCI Emerging Markets (USD denominated)'
            ),
            
            # Commodities
            'Gold_Futures': AssetMetadata(
                'Gold_Futures', 'commodity', 'Global', 'USD',
                'Gold Futures'
            ),
            'Oil_Brent_Futures': AssetMetadata(
                'Oil_Brent_Futures', 'commodity', 'Global', 'USD',
                'Brent Oil Futures'
            )
        }
        
    def _load_all_data(self):
        """Load all data files"""
        logger.info("Loading market data and exchange rates...")
        
        # Load exchange rates
        self._load_exchange_rates()
        
        # Load risk-free rate
        self._load_risk_free_rate()
        
        # Load raw asset data
        self._load_raw_assets()
        
        # Convert to ILS and create unified returns matrix
        self._process_ils_data()
        
        logger.info(f"Successfully loaded {len(self.returns_data.columns)} ILS-denominated assets")
        logger.info(f"Data period: {self.returns_data.index[0]} to {self.returns_data.index[-1]}")
        logger.info(f"Risk-free rate range: {self.risk_free_rate.min():.2%} - {self.risk_free_rate.max():.2%}")
        
    def _load_exchange_rates(self):
        """Load all FX rate data to ILS"""
        fx_files = {
            'USD_ILS': 'clean_USD_ILS_FX.csv',
            'EUR_ILS': 'clean_EUR_ILS_FX.csv', 
            'GBP_ILS': 'clean_GBP_ILS_FX.csv',
            'JPY_ILS': 'clean_JPY_ILS_FX.csv',
            'INR_ILS': 'clean_INR_ILS_FX.csv'
        }
        
        for fx_pair, filename in fx_files.items():
            file_path = self.data_path / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                # Standardize column names
                df.columns = ['date', 'fx_rate']
                df['date'] = pd.to_datetime(df['date'])
                self.exchange_rates[fx_pair] = df.set_index('date').sort_index()
                logger.debug(f"Loaded {fx_pair}: {len(df)} observations")
            else:
                logger.warning(f"FX file not found: {filename}")
                
    def _load_risk_free_rate(self):
        """Load Bank of Israel risk-free rate"""
        rf_file = self.data_path / 'clean_Risk_Free_Rate_Israel.csv'
        if rf_file.exists():
            df = pd.read_csv(rf_file)
            # Standardize column names
            df.columns = ['date', 'rate']
            df['date'] = pd.to_datetime(df['date'])
            # Rate is already in decimal form in the data
            self.risk_free_rate = df.set_index('date')['rate'].sort_index()
            logger.debug(f"Loaded risk-free rate: {len(df)} observations")
        else:
            logger.error("Risk-free rate file not found")
            raise FileNotFoundError("clean_Risk_Free_Rate_Israel.csv not found")
            
    def _load_raw_assets(self):
        """Load all raw asset data"""
        # Get all clean_*.csv files except FX and risk-free rate
        asset_files = list(self.data_path.glob('clean_*.csv'))
        
        exclude_files = {
            'clean_USD_ILS_FX.csv', 'clean_EUR_ILS_FX.csv', 'clean_GBP_ILS_FX.csv',
            'clean_JPY_ILS_FX.csv', 'clean_INR_ILS_FX.csv', 'clean_Risk_Free_Rate_Israel.csv'
        }
        
        for file_path in asset_files:
            if file_path.name not in exclude_files:
                asset_name = file_path.name.replace('clean_', '').replace('.csv', '')
                
                try:
                    df = pd.read_csv(file_path)
                    # Standardize column names
                    df.columns = ['date', 'price']
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date').set_index('date')
                    
                    # For daily data, convert to monthly first to avoid issues
                    # Check if this looks like daily data (more than 100 obs/year)
                    years = (df.index[-1] - df.index[0]).days / 365.25
                    obs_per_year = len(df) / years
                    
                    if obs_per_year > 100:  # Daily data
                        # Resample to month-end and calculate monthly returns
                        monthly_prices = df['price'].resample('ME').last()
                        monthly_returns = monthly_prices.pct_change().dropna()
                        df = pd.DataFrame({'return': monthly_returns})
                        logger.debug(f"Converted daily data to monthly: {len(df)} monthly observations")
                    else:
                        # Already monthly or lower frequency
                        df['return'] = df['price'].pct_change()
                        df = df[['return']].dropna()
                        logger.debug(f"Using data as-is: {len(df)} observations")
                    
                    if len(df) > 0:
                        self.raw_assets[asset_name] = df
                        logger.debug(f"Loaded {asset_name}: {len(df)} observations")
                    else:
                        logger.warning(f"No valid data for {asset_name}")
                    
                except Exception as e:
                    logger.error(f"Error loading {asset_name}: {e}")
                    
    def _process_ils_data(self):
        """Convert all assets to ILS and create unified returns matrix"""
        logger.info("Converting assets to ILS...")
        
        ils_assets = {}
        
        for asset_name, raw_data in self.raw_assets.items():
            metadata = self.asset_metadata.get(asset_name)
            if not metadata:
                logger.warning(f"No metadata for {asset_name}, assuming ILS")
                currency = 'ILS'
            else:
                currency = metadata.currency
                
            if currency == 'ILS':
                # Already in ILS
                ils_assets[asset_name] = raw_data['return']
            else:
                # Convert to ILS
                fx_key = f'{currency}_ILS'
                if fx_key in self.exchange_rates:
                    ils_return = self._convert_asset_to_ils(
                        raw_data, self.exchange_rates[fx_key], asset_name
                    )
                    if ils_return is not None:
                        ils_assets[asset_name] = ils_return
                else:
                    logger.warning(f"No FX rate for {currency}, skipping {asset_name}")
        
        # Create unified returns DataFrame
        if ils_assets:
            self.returns_data = pd.DataFrame(ils_assets)
            
            # Align with risk-free rate dates
            common_dates = self.returns_data.index.intersection(self.risk_free_rate.index)
            self.returns_data = self.returns_data.loc[common_dates]
            self.risk_free_rate = self.risk_free_rate.loc[common_dates]
            
            # Forward-fill missing values and drop remaining NaNs
            self.returns_data = self.returns_data.ffill().dropna()
            
            # Calculate excess returns and statistics
            self._calculate_statistics()
        else:
            logger.error("No assets successfully loaded")
            raise ValueError("No valid assets found")
            
    def _convert_asset_to_ils(self, asset_data: pd.DataFrame, 
                             fx_data: pd.DataFrame, 
                             asset_name: str) -> Optional[pd.Series]:
        """Convert single asset returns to ILS using FX rates"""
        try:
            # Convert FX data to monthly if needed (matching asset data frequency)
            asset_returns = asset_data['return']
            
            # Check if asset data is monthly (asset_returns should already be monthly from _load_raw_assets)
            asset_years = (asset_returns.index[-1] - asset_returns.index[0]).days / 365.25
            asset_freq = len(asset_returns) / asset_years
            
            if asset_freq < 50:  # Monthly data, need monthly FX too
                # Convert daily FX to monthly
                fx_monthly = fx_data.resample('ME').last()
                fx_returns = fx_monthly['fx_rate'].pct_change().dropna()
                
                # Align monthly asset returns with monthly FX returns
                common_dates = asset_returns.index.intersection(fx_returns.index)
                if len(common_dates) < 10:
                    logger.warning(f"Insufficient date overlap for {asset_name}")
                    return None
                
                aligned_asset = asset_returns.loc[common_dates]
                aligned_fx = fx_returns.loc[common_dates]
                
                # ILS return = (1 + foreign return) * (1 + fx return) - 1
                ils_return = (1 + aligned_asset) * (1 + aligned_fx) - 1
                
                return ils_return.dropna()
            else:
                # Use old method for daily data (shouldn't happen now)
                asset_df = asset_data.reset_index()
                fx_df = fx_data.reset_index()
                
                merged = pd.merge_asof(
                    asset_df.sort_values('date'),
                    fx_df.sort_values('date'), 
                    on='date',
                    direction='backward'
                )
                
                if merged.empty or 'fx_rate' not in merged.columns:
                    logger.warning(f"FX alignment failed for {asset_name}")
                    return None
                
                merged = merged.set_index('date').sort_index()
                fx_return = merged['fx_rate'].pct_change()
                ils_return = (1 + merged['return']) * (1 + fx_return) - 1
                
                return ils_return.dropna()
            
        except Exception as e:
            logger.error(f"Error converting {asset_name} to ILS: {e}")
            return None
            
    def _calculate_statistics(self):
        """Calculate mean returns and covariance matrix in ILS terms"""
        
        # Align risk-free rate with returns
        aligned_rf = self.risk_free_rate.reindex(self.returns_data.index, method='ffill')
        
        # Convert annual risk-free rate to monthly
        monthly_rf = (1 + aligned_rf)**(1/12) - 1
        
        # Calculate excess returns (subtract risk-free rate)
        excess_returns = self.returns_data.subtract(monthly_rf, axis=0)
        
        # Detect data frequency and annualize correctly
        n_obs = len(self.returns_data)
        years = (self.returns_data.index[-1] - self.returns_data.index[0]).days / 365.25
        periods_per_year = n_obs / years
        
        logger.info(f"Detected data frequency: {periods_per_year:.0f} observations per year")
        
        # Annualized statistics using detected frequency
        self.mean_returns = excess_returns.mean() * periods_per_year
        self.cov_matrix = excess_returns.cov() * periods_per_year
        
        # Store average annual risk-free rate for calculations
        self.avg_risk_free_rate = aligned_rf.mean()
        
        logger.info("Calculated ILS-denominated statistics:")
        logger.info(f"Average risk-free rate: {self.avg_risk_free_rate:.2%}")
        logger.info(f"Mean excess returns range: {self.mean_returns.min():.2%} to {self.mean_returns.max():.2%}")
        logger.info(f"Volatility range: {np.sqrt(np.diag(self.cov_matrix)).min():.2%} to {np.sqrt(np.diag(self.cov_matrix)).max():.2%}")
        
    def get_asset_indices_by_category(self, category: str) -> List[int]:
        """Get asset indices for a specific category"""
        indices = []
        for i, asset_name in enumerate(self.returns_data.columns):
            metadata = self.asset_metadata.get(asset_name)
            if metadata and metadata.category == category:
                indices.append(i)
        return indices
        
    def get_asset_names(self) -> List[str]:
        """Get list of all asset names"""
        return list(self.returns_data.columns)
        
    def get_returns_matrix(self) -> pd.DataFrame:
        """Get returns matrix aligned with risk-free rate"""
        return self.returns_data
        
    def get_risk_free_rate_series(self) -> pd.Series:
        """Get risk-free rate series aligned with returns (monthly)"""
        aligned_rf = self.risk_free_rate.reindex(self.returns_data.index, method='ffill')
        # Convert annual to monthly
        return (1 + aligned_rf)**(1/12) - 1
        
    def summary_statistics(self) -> Dict:
        """Get summary statistics for all assets"""
        stats = {}
        
        for asset_name in self.returns_data.columns:
            returns = self.returns_data[asset_name]
            annual_return = returns.mean() * 12 + self.avg_risk_free_rate
            annual_vol = returns.std() * np.sqrt(12)
            sharpe = (annual_return - self.avg_risk_free_rate) / annual_vol if annual_vol > 0 else 0
            
            metadata = self.asset_metadata.get(asset_name)
            
            stats[asset_name] = {
                'annual_return': annual_return,
                'annual_volatility': annual_vol,
                'sharpe_ratio': sharpe,
                'category': metadata.category if metadata else 'unknown',
                'region': metadata.region if metadata else 'unknown',
                'description': metadata.description if metadata else asset_name
            }
            
        return stats