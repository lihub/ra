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

## Data Processing Status
Successfully processed **21 asset classes** from raw data:

### Equity Assets (12)
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
- **US_REIT_Select (8.12% return, 20.99% vol, Sharpe 0.39) - NEW**

### Bond Assets (2) 
- US_Gov_Bonds_3_7Y (-0.28% return, 3.97% vol, Sharpe -0.07)
- **US_Gov_Bonds_Short (-0.18% return, 1.48% vol, Sharpe -0.12) - FIXED**

### Currency Assets (5)  
- USD_ILS_FX (-0.27% return, 7.67% vol, Sharpe -0.04)
- EUR_ILS_FX (-1.45% return, 8.62% vol, Sharpe -0.17)
- GBP_ILS_FX (-1.32% return, 9.42% vol, Sharpe -0.14)
- JPY_ILS_FX (-2.81% return, 11.38% vol, Sharpe -0.25)
- INR_ILS_FX (-4.11% return, 8.84% vol, Sharpe -0.46)

### Commodity Assets (2)
- Gold_Futures (8.33% return, 16.04% vol, Sharpe 0.52)
- Oil_Brent_Futures (5.07% return, 35.05% vol, Sharpe 0.14)

### Risk-Free Rate (1) - NEW
- **Risk_Free_Rate_Israel (0.1%-4.8% rate range, normalized monthly) - NEW**

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