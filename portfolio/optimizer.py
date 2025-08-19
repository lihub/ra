import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple
import os

class PortfolioOptimizer:
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.etf_data = {}
        self.returns = None
        self.cov_matrix = None
        self.mean_returns = None
        self.risk_free_rate = 0.02  # 2% risk-free rate
        
    def load_etf_data(self) -> None:
        """Load and process ETF data from CSV files"""
        etf_files = {
            'US_Large_Cap': 'S&P 500 TR Historical Data.csv',
            'US_Small_Cap': 'IWM - נתונים היסטורים תעודה ראסל 2000.csv',
            'NASDAQ': 'NASDAQ Composite Total Return Historical Data.csv',
            'Europe': 'MSCI International Europe Gross EUR - נתונים היסטוריים.csv',
            'Japan': 'MSCI International Japan Gross Real time Historical Data.csv',
            'Emerging_Markets': 'MSCI International EM Gross Real time Historical Data.csv',
            'Gov_Bonds_3_7': 'IEI - נתונים היסטורים תעודה ממשלתי 3-7.csv',
            'Gov_Bonds_Short': 'SCHO - נתונים היסטורים תעודה ממשלתי קצר.csv',
            'Gold': 'חוזים עתידיים על זהב - נתונים היסטוריים.csv',
            'Oil': 'חוזים עתידיים על נפט ברנט - נתונים היסטוריים.csv'
        }
        
        for etf_name, filename in etf_files.items():
            file_path = os.path.join(self.data_path, filename)
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                    # Parse dates with proper format (try multiple formats)
                    if 'תאריך' in df.columns:  # Hebrew date column
                        date_col = 'תאריך'
                    elif 'Date' in df.columns:
                        date_col = 'Date'
                    else:
                        continue  # Skip if no date column found
                    
                    # Try multiple date formats
                    for date_format in ['%d.%m.%Y', '%m/%d/%Y', '%Y-%m-%d', 'mixed']:
                        try:
                            if date_format == 'mixed':
                                df['Date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
                            else:
                                df['Date'] = pd.to_datetime(df[date_col], format=date_format, errors='coerce')
                            break
                        except:
                            continue
                    
                    # Find price column (various possible names including Hebrew "שער")
                    price_col = None
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(word in col_lower for word in ['price', 'close', 'last', 'final']):
                            price_col = col
                            break
                        if any(word in str(col) for word in ['מחיר', 'סגירה', 'אחרון', 'שער']):
                            price_col = col
                            break
                    
                    # If no explicit price column, find best numeric column
                    if not price_col:
                        for col in df.columns[1:]:  # Skip date column
                            try:
                                test_data = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                                if test_data.notna().sum() > len(df) * 0.8 and test_data.mean() > 0:
                                    price_col = col
                                    break
                            except:
                                continue
                    
                    if price_col:
                        df[price_col] = pd.to_numeric(df[price_col].astype(str).str.replace(',', ''), errors='coerce')
                        df = df.dropna(subset=['Date', price_col])
                        df = df.sort_values('Date')
                        clean_data = df[['Date', price_col]].rename(columns={price_col: 'Price'})
                        
                        if len(clean_data) > 100:  # Need sufficient data for optimization
                            self.etf_data[etf_name] = clean_data
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    def calculate_returns(self) -> None:
        """Calculate daily returns for all ETFs"""
        if not self.etf_data:
            self.load_etf_data()
        
        returns_data = {}
        for etf_name, data in self.etf_data.items():
            data['Returns'] = data['Price'].pct_change()
            returns_data[etf_name] = data[['Date', 'Returns']].dropna()
        
        # Align dates and create returns matrix
        common_dates = None
        for etf_name, data in returns_data.items():
            if common_dates is None:
                common_dates = set(data['Date'])
            else:
                common_dates = common_dates.intersection(set(data['Date']))
        
        common_dates = sorted(list(common_dates))
        
        returns_matrix = []
        etf_names = []
        for etf_name, data in returns_data.items():
            aligned_returns = []
            data_dict = dict(zip(data['Date'], data['Returns']))
            for date in common_dates:
                if date in data_dict:
                    aligned_returns.append(data_dict[date])
                else:
                    aligned_returns.append(0)  # Fill missing with 0
            returns_matrix.append(aligned_returns)
            etf_names.append(etf_name)
        
        self.returns = pd.DataFrame(np.array(returns_matrix).T, columns=etf_names)
        self.mean_returns = self.returns.mean() * 252  # Annualized
        self.cov_matrix = self.returns.cov() * 252    # Annualized
    
    def portfolio_stats(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """Calculate portfolio return, volatility, and Sharpe ratio"""
        portfolio_return = np.sum(self.mean_returns * weights)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
        return portfolio_return, portfolio_vol, sharpe_ratio
    
    def negative_sharpe(self, weights: np.ndarray) -> float:
        """Objective function to minimize (negative Sharpe ratio)"""
        return -self.portfolio_stats(weights)[2]
    
    def optimize_portfolio(self, risk_level: int = 5, max_volatility: float = None) -> Dict:
        """
        Optimize portfolio for maximum Sharpe ratio
        risk_level: 1-10 scale, higher = more risk tolerance
        """
        if self.returns is None:
            self.calculate_returns()
        
        n_assets = len(self.mean_returns)
        
        # Filter out assets with unrealistic returns (likely data errors)
        valid_assets = []
        valid_returns = []
        valid_cov_rows = []
        
        for i, (asset, ret) in enumerate(self.mean_returns.items()):
            # Filter out assets with extreme negative returns (data errors)
            if ret > -0.5:  # Allow up to -50% annual return max
                valid_assets.append(asset)
                valid_returns.append(ret)
                valid_cov_rows.append(i)
        
        if len(valid_assets) < 2:
            raise ValueError("Insufficient valid assets for optimization")
        
        # Create filtered datasets
        filtered_mean_returns = pd.Series(valid_returns, index=valid_assets)
        filtered_cov_matrix = self.cov_matrix.iloc[valid_cov_rows, valid_cov_rows]
        
        def filtered_portfolio_stats(weights):
            portfolio_return = np.sum(filtered_mean_returns * weights)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(filtered_cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
            return portfolio_return, portfolio_vol, sharpe_ratio
        
        def filtered_negative_sharpe(weights):
            return -filtered_portfolio_stats(weights)[2]
        
        # Set volatility constraint based on risk level
        if max_volatility is None:
            # Risk level 1 = 8% max vol, Risk level 10 = 25% max vol
            max_volatility = 0.08 + (risk_level - 1) * (0.25 - 0.08) / 9
        
        # Risk-adjusted asset allocation limits
        if risk_level <= 3:  # Conservative
            max_single_asset = 0.35
            min_bonds = 0.2  # Force minimum bond allocation
        elif risk_level <= 7:  # Moderate
            max_single_asset = 0.4
            min_bonds = 0.1
        else:  # Aggressive
            max_single_asset = 0.5
            min_bonds = 0.0
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        ]
        
        # Add volatility constraint
        def vol_constraint(weights):
            return max_volatility - filtered_portfolio_stats(weights)[1]
        
        constraints.append({'type': 'ineq', 'fun': vol_constraint})
        
        # Add minimum bond allocation for conservative portfolios
        if min_bonds > 0:
            bond_indices = [i for i, asset in enumerate(valid_assets) if 'Bond' in asset]
            if bond_indices:
                def min_bonds_constraint(weights):
                    return np.sum([weights[i] for i in bond_indices]) - min_bonds
                constraints.append({'type': 'ineq', 'fun': min_bonds_constraint})
        
        # Dynamic bounds based on risk level
        bounds = tuple((0, max_single_asset) for _ in range(len(valid_assets)))
        
        # Risk-adjusted initial guess
        if risk_level <= 3:  # Conservative start
            x0 = np.array([0.3 if 'Bond' in asset else 0.7/max(1, len(valid_assets)-1) 
                          for asset in valid_assets])
        else:  # Balanced start
            x0 = np.array([1/len(valid_assets)] * len(valid_assets))
        
        x0 = x0 / np.sum(x0)  # Normalize
        
        # Optimize
        result = minimize(
            filtered_negative_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        optimal_weights = result.x
        port_return, port_vol, sharpe = filtered_portfolio_stats(optimal_weights)
        
        # Create allocation dictionary (map back to original assets)
        allocation = {}
        for i, asset in enumerate(valid_assets):
            if optimal_weights[i] > 0.01:  # Only include assets with >1% allocation
                allocation[asset] = round(optimal_weights[i], 4)
        
        # Generate historical performance data (need to map weights back to full dataset)
        full_weights = np.zeros(len(self.mean_returns))
        for i, asset in enumerate(valid_assets):
            original_idx = list(self.mean_returns.index).index(asset)
            full_weights[original_idx] = optimal_weights[i]
        
        performance_data = self.generate_performance_history(full_weights)
        
        return {
            'allocation': allocation,
            'expected_return': round(port_return, 4),
            'volatility': round(port_vol, 4),
            'sharpe_ratio': round(sharpe, 4),
            'optimization_success': result.success,
            'performance_history': performance_data
        }
    
    def generate_performance_history(self, weights: np.ndarray, initial_value: float = 10000) -> Dict:
        """Generate historical cumulative P/L for the optimized portfolio"""
        if self.returns is None:
            return {}
        
        # Calculate portfolio daily returns
        portfolio_returns = (self.returns * weights).sum(axis=1)
        
        # Calculate cumulative value over time
        cumulative_returns = (1 + portfolio_returns).cumprod()
        portfolio_values = initial_value * cumulative_returns
        
        # Get dates (approximate - using index as days from start)
        dates = pd.date_range(start='2020-01-01', periods=len(portfolio_values), freq='D')
        
        # Convert to list of dictionaries for JSON serialization
        performance_data = []
        for i, (date, value) in enumerate(zip(dates, portfolio_values)):
            if i % 7 == 0:  # Sample every 7 days to reduce data size
                performance_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': round(value, 2),
                    'pnl': round(value - initial_value, 2),
                    'pnl_percent': round((value - initial_value) / initial_value * 100, 2)
                })
        
        # Add summary statistics
        final_value = portfolio_values.iloc[-1]
        total_return = (final_value - initial_value) / initial_value
        max_value = portfolio_values.max()
        min_value = portfolio_values.min()
        max_drawdown = (portfolio_values / portfolio_values.expanding().max() - 1).min()
        
        return {
            'timeseries': performance_data,
            'summary': {
                'initial_value': initial_value,
                'final_value': round(final_value, 2),
                'total_return_percent': round(total_return * 100, 2),
                'max_value': round(max_value, 2),
                'min_value': round(min_value, 2),
                'max_drawdown_percent': round(max_drawdown * 100, 2)
            }
        }