#!/usr/bin/env python3
"""
Process ALL raw data files and save to processed_data folder
NEVER modifies raw data - only reads and processes into clean files
"""
import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

class RawDataProcessor:
    def __init__(self, raw_data_path="raw_data/", processed_data_path="processed_data/"):
        self.raw_data_path = raw_data_path
        self.processed_data_path = processed_data_path
        self.processed_count = 0
        self.failed_count = 0
        
        # Ensure processed_data directory exists
        os.makedirs(processed_data_path, exist_ok=True)
        
        # Asset type mapping based on filename patterns
        self.asset_types = {
            'S&P 500 TR': ('US_Large_Cap_SP500', 'equity'),
            'NASDAQ Composite': ('NASDAQ_Total_Return', 'equity'),
            'IWM': ('US_Small_Cap_Russell2000', 'equity'),
            'MSCI International EM': ('Emerging_Markets_MSCI', 'equity'),
            'MSCI International Europe': ('Europe_MSCI', 'equity'),
            'MSCI International Japan': ('Japan_MSCI', 'equity'),
            'CAC 40': ('France_CAC40', 'equity'),
            'FTSE 100': ('UK_FTSE100', 'equity'),
            'דאקס': ('Germany_DAX', 'equity'),
            'NIFTY': ('India_NIFTY', 'equity'),
            'IEI': ('US_Gov_Bonds_3_7Y', 'bond'),
            'SCHO': ('US_Gov_Bonds_Short', 'bond'),
            'תל בונד 60': ('Israel_TelBond_60', 'bond'),
            'תל בונד שיקלי': ('Israel_TelBond_Shekel', 'bond'),
            'תל גוב צמוד 0-2': ('Israel_Gov_Indexed_0_2Y', 'bond'),
            'תל גוב צמודות 5-10': ('Israel_Gov_Indexed_5_10Y', 'bond'),
            'תל גוב שיקלי 0-2': ('Israel_Gov_Shekel_0_2Y', 'bond'),
            'תל גוב שיקלי 5-10': ('Israel_Gov_Shekel_5_10Y', 'bond'),
            'תא 125': ('Israel_TA125', 'equity'),
            'sme60': ('Israel_SME60', 'equity'),
            'זהב': ('Gold_Futures', 'commodity'),
            'נפט ברנט': ('Oil_Brent_Futures', 'commodity'),
            'USD_ILS': ('USD_ILS_FX', 'currency'),
            'EUR_ILS': ('EUR_ILS_FX', 'currency'),
            'GBP_ILS': ('GBP_ILS_FX', 'currency'),
            'JPY_ILS': ('JPY_ILS_FX', 'currency'),
            'INR_ILS': ('INR_ILS_FX', 'currency'),
            'Dow Jones U.S. Select REIT': ('US_REIT_Select', 'reit'),
            'risk_free_rate': ('Risk_Free_Rate_Israel', 'risk_free')
        }
    
    def identify_asset_type(self, filename):
        """Identify asset type and clean name from filename"""
        for pattern, (clean_name, asset_type) in self.asset_types.items():
            if pattern in filename:
                return clean_name, asset_type
        
        # Default fallback
        base_name = filename.replace('.csv', '').replace(' - נתונים היסטוריים', '').replace(' Historical Data', '')
        clean_name = base_name.replace(' ', '_').replace('-', '_')
        return clean_name, 'unknown'
    
    def process_risk_free_rate(self, filepath):
        """Special processing for risk-free rate data to normalize granularity"""
        print(f"[INFO] Processing risk-free rate data with normalization...")
        
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            
            # Parse dates
            df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y')
            df = df.sort_values('date').dropna()
            
            # Convert interest rate from annual percentage to decimal
            df['rate'] = df['interest rate'] / 100.0
            
            # Create monthly series by forward-filling rates
            date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='M')
            monthly_df = pd.DataFrame({'Date': date_range})
            
            # For each month, find the most recent rate that was active
            monthly_rates = []
            for date in monthly_df['Date']:
                # Find the most recent rate decision before or on this date
                active_rates = df[df['date'] <= date]
                if len(active_rates) > 0:
                    rate = active_rates.iloc[-1]['rate']
                    monthly_rates.append(rate)
                else:
                    monthly_rates.append(np.nan)
            
            monthly_df['Price'] = monthly_rates
            monthly_df = monthly_df.dropna()
            
            # Save processed data
            output_path = os.path.join(self.processed_data_path, "clean_Risk_Free_Rate_Israel.csv")
            monthly_df.to_csv(output_path, index=False)
            
            print(f"  [SUCCESS] Normalized risk-free rate to {len(monthly_df)} monthly points")
            print(f"  Rate range: {monthly_df['Price'].min():.3f} to {monthly_df['Price'].max():.3f}")
            print(f"  [SAVED] clean_Risk_Free_Rate_Israel.csv (risk_free)")
            
            return True
            
        except Exception as e:
            print(f"  [ERROR] Processing risk-free rate: {str(e)}")
            return False

    def process_single_file(self, filepath):
        """Process a single CSV file from raw_data"""
        filename = os.path.basename(filepath)
        
        # Special handling for risk-free rate
        if 'risk_free_rate' in filename:
            return self.process_risk_free_rate(filepath)
        
        # Handle Unicode filenames for display
        try:
            display_name = filename
        except:
            display_name = "[Hebrew filename]"
        
        print(f"[INFO] Processing file...")
        
        # Skip non-CSV files
        if not filename.endswith('.csv'):
            print(f"  [SKIP] Not a CSV file")
            return False
        
        try:
            # Load the raw file (NEVER modify it)
            df = pd.read_csv(filepath, encoding='utf-8')
            
            if len(df) < 10:
                print(f"  [ERROR] Insufficient data: {len(df)} rows")
                return False
            
            print(f"  Shape: {df.shape}")
            
            # Find date column
            date_col = None
            for col_name in ['Date', 'תאריך', 'date']:
                if col_name in df.columns:
                    date_col = col_name
                    break
            
            if not date_col:
                print(f"  [ERROR] No date column found")
                return False
            
            # Find price column
            price_col = None
            
            # Try specific price column names first
            price_candidates = ['Price', 'Close', 'Last', 'מחיר', 'סגירה', 'אחרון', 'שער']
            for col_name in price_candidates:
                if col_name in df.columns:
                    price_col = col_name
                    break
            
            # If no exact match, find best numeric column
            if not price_col:
                for col in df.columns:
                    if col == date_col:
                        continue
                    try:
                        # Test if column can be converted to numeric
                        test_data = df[col].astype(str).str.replace(',', '').str.replace('%', '')
                        numeric_data = pd.to_numeric(test_data, errors='coerce')
                        valid_pct = numeric_data.notna().sum() / len(df)
                        mean_val = numeric_data.mean()
                        
                        # Good price column criteria
                        if (valid_pct > 0.8 and  # >80% valid data
                            mean_val > 0 and      # Positive values
                            numeric_data.std() > 0):  # Has variation
                            price_col = col
                            break
                    except:
                        continue
            
            if not price_col:
                print(f"  [ERROR] No suitable price column found")
                return False
            
            print(f"  Using date column: [found]")
            print(f"  Using price column: [found]")
            
            # Create working copy for processing
            df_work = df[[date_col, price_col]].copy()
            
            # Parse dates with multiple format attempts
            df_work['Date_Parsed'] = None
            date_formats = ['%m/%d/%Y', '%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']
            
            for date_format in date_formats:
                try:
                    parsed_dates = pd.to_datetime(df_work[date_col], format=date_format, errors='coerce')
                    valid_count = parsed_dates.notna().sum()
                    if valid_count > len(df_work) * 0.8:
                        df_work['Date_Parsed'] = parsed_dates
                        print(f"  Dates parsed with format {date_format}: {valid_count}/{len(df_work)}")
                        break
                except:
                    continue
            
            # Try flexible parsing if no format worked
            if df_work['Date_Parsed'].isna().all():
                try:
                    df_work['Date_Parsed'] = pd.to_datetime(df_work[date_col], dayfirst=True, errors='coerce')
                    valid_count = df_work['Date_Parsed'].notna().sum()
                    if valid_count > len(df_work) * 0.5:
                        print(f"  Dates parsed flexibly: {valid_count}/{len(df_work)}")
                    else:
                        print(f"  [ERROR] Could not parse dates")
                        return False
                except:
                    print(f"  [ERROR] Date parsing failed")
                    return False
            
            # Clean price data
            price_data = df_work[price_col].astype(str).str.replace(',', '').str.replace('%', '')
            df_work['Price_Clean'] = pd.to_numeric(price_data, errors='coerce')
            
            # Filter to valid data only (and historical data only)
            today = pd.Timestamp.now()
            valid_mask = (
                df_work['Date_Parsed'].notna() & 
                df_work['Price_Clean'].notna() & 
                (df_work['Price_Clean'] > 0) &
                (df_work['Date_Parsed'] <= today)
            )
            
            clean_data = df_work[valid_mask].copy()
            
            if len(clean_data) < 50:
                print(f"  [ERROR] Insufficient clean data: {len(clean_data)} points")
                return False
            
            # Sort chronologically
            clean_data = clean_data.sort_values('Date_Parsed')
            
            # Apply specific data fixes for known problematic datasets
            if 'SCHO' in filename or 'US_Gov_Bonds_Short' in filename:
                # Fix for US Gov Bonds Short: Remove impossible price jumps from ~$25 to ~$52
                original_count = len(clean_data)
                clean_data = clean_data[clean_data['Price_Clean'] <= 30].copy()
                if len(clean_data) < original_count:
                    removed = original_count - len(clean_data)
                    print(f"  [FIXED] Removed {removed} impossible price jumps (prices >$30) for short bonds")
            
            # Create final output
            final_df = clean_data[['Date_Parsed', 'Price_Clean']].rename(columns={
                'Date_Parsed': 'Date',
                'Price_Clean': 'Price'
            }).reset_index(drop=True)
            
            # Calculate basic statistics for validation
            returns = final_df['Price'].pct_change().dropna()
            if len(returns) > 10:
                annual_return = returns.mean() * 252
                annual_vol = returns.std() * np.sqrt(252)
                sharpe = annual_return / annual_vol if annual_vol > 0 else 0
                
                date_range = f"{final_df['Date'].min().strftime('%Y-%m-%d')} to {final_df['Date'].max().strftime('%Y-%m-%d')}"
                print(f"  [SUCCESS] {len(final_df)} points from {date_range}")
                print(f"  Annual Return: {annual_return:.2%}, Volatility: {annual_vol:.2%}, Sharpe: {sharpe:.2f}")
                
                # Identify asset type and create clean filename
                clean_name, asset_type = self.identify_asset_type(filename)
                output_filename = f"clean_{clean_name}.csv"
                output_path = os.path.join(self.processed_data_path, output_filename)
                
                # Save processed data
                final_df.to_csv(output_path, index=False)
                print(f"  [SAVED] {output_filename} ({asset_type})")
                
                # Flag suspicious data
                if abs(annual_return) > 0.5 or annual_vol > 1.0:
                    print(f"  [WARNING] Check data quality - extreme values")
                
                return True
            else:
                print(f"  [ERROR] Insufficient return data")
                return False
                
        except Exception as e:
            print(f"  [ERROR] {str(e)[:100]}")
            return False
    
    def process_all_files(self):
        """Process all CSV files in raw_data directory"""
        print("PROCESSING ALL RAW DATA FILES")
        print("="*50)
        print(f"Source: {self.raw_data_path}")
        print(f"Target: {self.processed_data_path}")
        print(f"CRITICAL: Raw data files will NOT be modified")
        print("="*50)
        
        # Find all CSV files
        csv_pattern = os.path.join(self.raw_data_path, "*.csv")
        csv_files = glob.glob(csv_pattern)
        
        print(f"Found {len(csv_files)} CSV files to process")
        
        for filepath in csv_files:
            success = self.process_single_file(filepath)
            if success:
                self.processed_count += 1
            else:
                self.failed_count += 1
        
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Successfully processed: {self.processed_count} files")
        print(f"Failed to process: {self.failed_count} files")
        
        # List all processed files
        processed_files = glob.glob(os.path.join(self.processed_data_path, "clean_*.csv"))
        if processed_files:
            print(f"\nProcessed files saved to {self.processed_data_path}:")
            for filepath in sorted(processed_files):
                filename = os.path.basename(filepath)
                print(f"  {filename}")
        
        return self.processed_count, self.failed_count

def main():
    """Main execution"""
    processor = RawDataProcessor()
    success_count, failure_count = processor.process_all_files()
    
    if success_count > 0:
        print(f"\n[SUCCESS] {success_count} files processed and saved to processed_data/")
    if failure_count > 0:
        print(f"[INFO] {failure_count} files could not be processed (check logs above)")
    
    return processor

if __name__ == "__main__":
    processor = main()