# Roboadvisor Project

## Project Overview
Building a lean web application for portfolio optimization based on risk tolerance. The application will:
- Allow users to select their risk level
- Generate optimal portfolios using available ETF data
- Start with core functionality and expand to full roboadvisor features

## Available ETF Data
The `/raw_data` folder contains historical data for various ETFs and indices:

**CRITICAL: NEVER MODIFY RAW DATA FILES**
- Raw data files in `/raw_data` must NEVER be edited or modified
- Always process raw data and save results to `/processed_data` folder
- Raw data serves as the source of truth and must remain unchanged
- Use `process_all_raw_data.py` to convert raw data to clean CSV files in `/processed_data`

## Data Processing Status
Successfully processed **19 asset classes** from raw data:

### Equity Assets (11)
- US_Large_Cap_SP500 (14.41% return, 17.49% vol, Sharpe 0.82)
- NASDAQ_Total_Return (16.95% return, 21.33% vol, Sharpe 0.79) 
- US_Small_Cap_Russell2000 (10.39% return, 22.31% vol, Sharpe 0.47)
- Europe_MSCI (8.52% return, 15.92% vol, Sharpe 0.53)
- Japan_MSCI (8.37% return, 18.59% vol, Sharpe 0.45)
- Emerging_Markets_MSCI (6.30% return, 15.60% vol, Sharpe 0.40)
- Germany_DAX (10.72% return, 19.51% vol, Sharpe 0.55)
- France_CAC40 (9.34% return, 19.60% vol, Sharpe 0.48)
- UK_FTSE100 (8.31% return, 15.02% vol, Sharpe 0.55)
- India_NIFTY (12.65% return, 16.62% vol, Sharpe 0.76)

### Bond Assets (2)
- US_Gov_Bonds_3_7Y (-0.28% return, 3.97% vol, Sharpe -0.07)
- US_Gov_Bonds_Short (62.78% return, 125.43% vol - DATA QUALITY ISSUE)

### Currency Assets (5)  
- USD_ILS_FX (-0.27% return, 7.67% vol, Sharpe -0.04)
- EUR_ILS_FX (-1.45% return, 8.62% vol, Sharpe -0.17)
- GBP_ILS_FX (-1.32% return, 9.42% vol, Sharpe -0.14)
- JPY_ILS_FX (-2.81% return, 11.38% vol, Sharpe -0.25)
- INR_ILS_FX (-4.11% return, 8.84% vol, Sharpe -0.46)

### Commodity Assets (2)
- Gold_Futures (8.33% return, 16.04% vol, Sharpe 0.52)
- Oil_Brent_Futures (5.07% return, 35.05% vol, Sharpe 0.14)

### US Market ETFs
- **S&P 500 TR** - S&P 500 Total Return index
- **IWM** - iShares Russell 2000 ETF (small-cap)
- **NASDAQ Composite TR** - NASDAQ Total Return

### International ETFs
- **MSCI International EM** - Emerging Markets
- **MSCI International Europe** - European markets
- **MSCI International Japan** - Japanese markets
- **CAC 40**, **FTSE 100**, **DAX** - European indices
- **NIFTY** - Indian market

### Bond ETFs
- **IEI** - iShares 3-7 Year Treasury Bond ETF
- **SCHO** - Short-term government bonds
- **Tel Bond** variants - Israeli government bonds

### Currency Data
- Multiple currency pairs against ILS (USD, EUR, GBP, JPY, INR)

### Commodities
- Gold futures, Brent oil futures

## Development Guidelines

### 1. Portfolio Optimization Focus
- **Risk-based allocation** - Different portfolios for different risk levels
- **Diversification principles** - Spread across asset classes and geographies
- **Modern Portfolio Theory** - Optimize for risk-adjusted returns
- **Rebalancing logic** - Maintain target allocations

### 2. Data-Driven Decisions
- **Historical performance analysis** of available ETFs
- **Correlation analysis** between assets
- **Risk metrics calculation** (volatility, Sharpe ratio, max drawdown)
- **Currency hedging considerations** for international assets

### 3. User Experience Priorities
- **Simple risk assessment** - Easy-to-understand questionnaire
- **Clear portfolio visualization** - Show allocations and expected performance
- **Transparent methodology** - Explain why certain assets were chosen
- **Performance tracking** - Historical and projected returns

### 4. Technical Architecture
- **Lean and focused** - Start with core features only
- **Scalable design** - Plan for future feature additions
- **Efficient data processing** - Handle historical data calculations
- **Responsive web interface** - Works on desktop and mobile

## Roboadvisor Best Practices (Based on Market Leaders)
- **Automated rebalancing** - Maintain target allocations automatically
- **Tax optimization** - Consider tax-loss harvesting for larger portfolios
- **Goal-based planning** - Retirement, education, general wealth building
- **Low fees** - Competitive with market leaders (0.25-0.50% annually)
- **Educational content** - Help users understand their investments

## Code Quality Standards
- **Clean and maintainable** - Code should be easy to understand and modify
- **Well-tested** - Portfolio calculations need to be accurate
- **Performance-focused** - Efficient handling of large datasets
- **Security-conscious** - Protect user data and financial information