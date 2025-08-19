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