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

## Data Quality Fixes
The processor automatically applies data quality fixes for known issues:

### US Government Bonds Short (SCHO)
- **Issue**: Impossible price jumps from ~$25 to ~$52 causing extreme volatility (125.43% vol)
- **Fix**: Automatic removal of prices above $30 during processing
- **Result**: Realistic performance (-0.18% return, 1.48% vol) suitable for portfolio optimization
- **Implementation**: Built into `process_all_raw_data.py` for automatic application

### Risk-Free Rate Normalization
- **Issue**: Irregular central bank rate decisions (various frequencies)
- **Fix**: Forward-fill rates to create consistent monthly series
- **Result**: 187 monthly data points suitable for portfolio calculations
- **Range**: 0.1% to 4.8% (Bank of Israel rates 2010-2025)

## Critical Data Processing Fix (Session 2025-09-13)

### Major Bug Discovery and Resolution
**Issue**: Portfolio optimization was showing unrealistically low returns (0-1% annually) despite individual assets having much higher performance.

**Root Cause**: Daily data (3,916 observations over 15.6 years = 251 observations/year) was being treated as monthly data and annualized incorrectly using factor of 12 instead of 251.

**Investigation Process**:
1. **Debugging Pipeline**: Created `debug_return_calculation.py` to trace data through entire pipeline
2. **Currency Analysis**: Built `analyze_currency_impact.py` showing USD/ILS impact was minimal (-6.7% drag)  
3. **Individual Asset Check**: `sanity_check_returns.py` revealed S&P 500 actual performance was 13.7% annually
4. **Data Frequency Detection**: Found daily data was being processed as monthly returns

**Solution Implemented**:
- **Automatic Frequency Detection**: Data manager now detects daily vs monthly data (>100 obs/year = daily)
- **Daily-to-Monthly Conversion**: Daily prices converted to month-end, then monthly returns calculated
- **Proper FX Handling**: Currency conversion aligned with monthly frequency
- **Correct Annualization**: Monthly returns annualized using factor of 12

**Results After Fix**:
- **Individual Assets**: NASDAQ 18.5%, S&P 500 15.6%, Gold 14.6% annually (realistic)
- **Portfolio Performance**: 2.6-5.8% range (appropriate for diversified portfolios)
- **Risk-Return Profiles**: Conservative 2.6%, Moderate 5.6%, Aggressive 5.8%

### Currency Impact Analysis
**Created Comprehensive Analysis**:
- **US Assets**: USD/ILS impact minimal (-1.6% total change, -6.7% drag on S&P 500)
- **Indian Assets**: INR/ILS major impact (-51.6% currency change, NIFTY 11.9% INR vs 6.7% ILS annually)
- **Visualization**: Generated charts showing cumulative returns and currency effects

## Data Processing Status
Successfully processed **23 asset classes** with corrected daily-to-monthly conversion:

### Equity Assets (12) - CORRECTED PERFORMANCE (ILS Terms, 2017-2025)
- **NASDAQ_Total_Return (18.5% return, 15.7% vol, Sharpe 1.06) - CORRECTED**
- **US_Large_Cap_SP500 (15.6% return, 12.7% vol, Sharpe 1.09) - CORRECTED**
- **Israel_TA125 (14.1% return, 15.6% vol, Sharpe 0.79) - CORRECTED**
- **India_NIFTY (12.3% return, 18.2% vol, Sharpe 0.58) - CORRECTED**
- **Germany_DAX (10.3% return, 17.0% vol, Sharpe 0.50) - CORRECTED**
- **France_CAC40 (10.0% return, 16.5% vol, Sharpe 0.50) - CORRECTED**
- **Europe_MSCI (9.2% return, 13.7% vol, Sharpe 0.54) - CORRECTED**
- **Israel_SME60 (8.9% return, 20.5% vol, Sharpe 0.35) - CORRECTED**
- **UK_FTSE100 (8.6% return, 13.9% vol, Sharpe 0.49) - CORRECTED**
- **US_Small_Cap_Russell2000 (8.0% return, 18.7% vol, Sharpe 0.34) - CORRECTED**
- **US_REIT_Select (6.9% return, 16.2% vol, Sharpe 0.32) - CORRECTED**
- **Emerging_Markets_MSCI (6.8% return, 13.9% vol, Sharpe 0.36) - CORRECTED**
- **Japan_MSCI (4.9% return, 15.7% vol, Sharpe 0.20) - CORRECTED**

### Bond Assets (2) - CORRECTED PERFORMANCE (ILS Terms, 2017-2025)
- **US_Gov_Bonds_3_7Y (1.0% return, 7.7% vol, Sharpe -0.10) - CORRECTED**
- **US_Gov_Bonds_Short (1.1% return, 7.9% vol, Sharpe -0.09) - CORRECTED**

### Israeli Government/Corporate Bonds (6) - CORRECTED PERFORMANCE
- **Israel_TelBond_60 (4.5% return, 4.7% vol, Sharpe 0.58) - CORRECTED**
- **Israel_TelBond_Shekel (3.8% return, 4.9% vol, Sharpe 0.41) - CORRECTED**
- **Israel_Gov_Indexed_0_2Y (3.6% return, 1.6% vol, Sharpe 1.18) - CORRECTED**
- **Israel_Gov_Indexed_5_10Y (3.2% return, 4.8% vol, Sharpe 0.31) - CORRECTED**
- **Israel_Gov_Shekel_0_2Y (3.0% return, 0.8% vol, Sharpe 1.55) - CORRECTED**
- **Israel_Gov_Shekel_5_10Y (2.4% return, 4.6% vol, Sharpe 0.14) - CORRECTED**

### Commodity Assets (2) - CORRECTED PERFORMANCE (ILS Terms, 2017-2025)
- **Gold_Futures (14.6% return, 14.6% vol, Sharpe 0.88) - CORRECTED**
- **Oil_Brent_Futures (12.4% return, 37.7% vol, Sharpe 0.28) - CORRECTED**

### Risk-Free Rate (1)
- **Risk_Free_Rate_Israel (1.75% average annually, 2017-2025 period) - CORRECTED**

## Portfolio Optimization Results (After Fix)

### Typical Investor Performance (ILS Terms)
**Young Professional (Moderate Risk, 30yr horizon)**:
- Expected Return: 5.6% annually
- Volatility: 5.2%  
- Sharpe Ratio: 0.74
- Allocation: 30% Equity, 28% Israeli bonds, 22% US bonds, 20% Commodities

**Tech Entrepreneur (Very Aggressive, 25yr horizon)**:
- Expected Return: 5.8% annually
- Volatility: 9.1%
- Sharpe Ratio: 0.44  
- Allocation: 70% Equity, 16% Gold, 14% Bonds

**Retiree (Conservative, 5yr horizon)**:
- Expected Return: 2.6% annually
- Volatility: 2.6%
- Sharpe Ratio: 0.31
- Allocation: 57% Israeli bonds, 27% US bonds, 15% Equity, 1% Commodities

### Key Files Created/Modified This Session
- `portfolio/ils_data_manager.py` - **MAJOR FIX**: Daily-to-monthly conversion with frequency detection
- `debug_return_calculation.py` - Debugging pipeline to identify data issues
- `analyze_currency_impact.py` - US equity vs USD/ILS currency analysis  
- `analyze_indian_currency_impact.py` - Indian equity vs INR/ILS currency analysis
- `sanity_check_returns.py` - Individual asset performance validation
- `show_portfolio_examples.py` - Portfolio optimization examples (working correctly now)

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
- **SCHO** - Short-term government bonds (fixed data quality issues)
- **Tel Bond** variants - Israeli government bonds

### REIT ETFs
- **Dow Jones U.S. Select REIT** - US Real Estate Investment Trusts

### Currency Data
- Multiple currency pairs against ILS (USD, EUR, GBP, JPY, INR)

### Commodities
- Gold futures, Brent oil futures

### Risk-Free Rate
- **Bank of Israel interest rates** - Normalized monthly series (2010-2025)

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

## Current Tech Stack
**IMPORTANT: Always check the actual codebase before making assumptions about the tech stack**

- **Backend**: FastAPI (Python) - main.py contains the web server
- **Frontend**: Jinja2 templates + static CSS/JS (server-side rendering)
- **Data Processing**: Python scripts for portfolio optimization
- **Content Management**: Markdown-based multilingual system
- **KYC System**: Advanced risk assessment with behavioral questions
- **Deployment**: Railway hosting (Procfile indicates container deployment)
- **Data Storage**: CSV files for processed data, pickle files for caching

**Key Files:**
- `main.py` - FastAPI application with routes
- `templates/` - Jinja2 HTML templates
- `static/` - CSS and JavaScript files  
- `portfolio/` - Portfolio optimization engine
- `kyc/` - KYC risk assessment system
- `content/` - Multilingual content management
- `processed_data/` - Clean CSV data files

## Content Management System

The site uses a markdown-based content management system with full multilingual support:

**Structure:**
- `content/en/` - English content files
- `content/he/` - Hebrew content files
- Each page has its own `.md` file (e.g., `risk-assessment.md`, `homepage.md`)

**Content File Format:**
```markdown
# Page Title

## key_name_1
Content text here

## key_name_2
More content text
```

**Using Content in Templates:**
```html
<h1>{{ content.page_name('key_name_1') }}</h1>
<p>{{ content.page_name('key_name_2') }}</p>
```

**Adding New Content:**
1. Edit the appropriate `.md` files in `content/en/` and `content/he/`
2. Add new `## key_name` sections as needed
3. Use keys in templates with `{{ content.page_name('key_name') }}`
4. Reload content: Visit `/reload-content` endpoint or restart server

**IMPORTANT: Content Reloading**
- **Development**: Visit `http://localhost:8000/reload-content` to refresh content without restarting
- **Production**: Content is loaded once at startup for performance

## KYC Risk Assessment System

The site implements a sophisticated Know Your Customer (KYC) risk assessment system:

**Features:**
- **6 Behavioral Questions**: Scenario-based questions that reveal true risk tolerance
- **Real-time Validation**: Client-side inconsistency warnings as users answer
- **Consistency Rules**: 4 validation rules that detect contradictory responses
- **Risk Categorization**: Maps responses to 5 risk categories (Ultra Conservative → Very Aggressive)
- **Portfolio Constraints**: Each category defines max drawdown, volatility targets, and allocation limits
- **Multilingual Support**: Questions and warnings available in Hebrew and English

**KYC System Architecture:**
```
kyc/
├── __init__.py          # Module exports
├── models.py            # Data models (KYCResponse, RiskProfile)
├── constants.py         # Risk categories, questions, validation rules
├── risk_assessor.py     # Core assessment logic
└── validators.py        # Consistency validation
```

**Risk Categories:**
1. **Ultra Conservative** (0-25 points): 3% max drawdown, 4% volatility, 5-20% equity
2. **Conservative** (26-45 points): 8% max drawdown, 8% volatility, 15-40% equity
3. **Moderate** (46-65 points): 15% max drawdown, 12% volatility, 30-65% equity
4. **Aggressive** (66-85 points): 25% max drawdown, 18% volatility, 55-80% equity
5. **Very Aggressive** (86-100 points): 40% max drawdown, 22% volatility, 70-95% equity

**Flow:**
1. User answers 6 KYC questions
2. System validates responses for consistency
3. If inconsistent, warnings shown (errors block portfolio calculation)
4. Responses mapped to risk score and category
5. Portfolio optimizer uses category constraints
6. Results include KYC profile information

**Testing:**
- `test_kyc_backend.py` - Unit tests for KYC system
- `test_api_endpoint.py` - API integration tests

## Code Quality Standards
- **Clean and maintainable** - Code should be easy to understand and modify
- **Well-tested** - Portfolio calculations need to be accurate
- **Performance-focused** - Efficient handling of large datasets
- **Security-conscious** - Protect user data and financial information