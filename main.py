from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Roboadvisor", description="Portfolio Optimization Platform")

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/risk-assessment", response_class=HTMLResponse)
async def risk_assessment(request: Request):
    return templates.TemplateResponse("risk_assessment.html", {"request": request})

@app.post("/api/calculate-portfolio")
async def calculate_portfolio(
    risk_level: int = Form(...),
    investment_amount: float = Form(...),
    investment_duration: float = Form(10.0)
):
    import traceback
    
    try:
        print(f"Starting optimization for risk level {risk_level}, amount ${investment_amount}, duration {investment_duration} years")
        
        from portfolio.optimizer_v2 import AdvancedPortfolioOptimizer
        from portfolio.data_manager import MarketDataManager
        from portfolio.analytics import PortfolioAnalytics
        
        # Initialize components
        data_manager = MarketDataManager()
        analytics = PortfolioAnalytics()
        optimizer = AdvancedPortfolioOptimizer(data_manager, analytics)
        
        # Optimize portfolio with duration support
        result = optimizer.optimize_portfolio(
            risk_level=risk_level,
            investment_duration_years=investment_duration,
            investment_amount=investment_amount
        )
        
        print(f"Optimization completed successfully: {result.optimization_success}")
        
        # Convert allocation percentages to dollar amounts
        portfolio_dollars = {}
        for asset, weight in result.allocation.items():
            portfolio_dollars[asset] = round(investment_amount * weight, 2)
        
        # Get optimization insights
        insights = optimizer.get_optimization_insights(result, investment_duration)
        
        return {
            "risk_level": risk_level,
            "investment_amount": investment_amount,
            "investment_duration": investment_duration,
            "portfolio": result.allocation,
            "portfolio_dollars": portfolio_dollars,
            "expected_return": result.expected_return * 100,  # Convert to percentage
            "volatility": result.volatility * 100,  # Convert to percentage
            "sharpe_ratio": result.sharpe_ratio,
            "optimization_success": result.optimization_success,
            "constraints_satisfied": result.constraints_satisfied,
            "performance_history": result.performance_history,
            "insights": insights,
            "performance_metrics": {
                "max_drawdown": round(result.performance_metrics.max_drawdown * 100, 2),
                "sortino_ratio": round(result.performance_metrics.sortino_ratio, 2),
                "value_at_risk_95": round(result.performance_metrics.value_at_risk_95 * 100, 2),
                "winning_periods": round(result.performance_metrics.winning_periods * 100, 1)
            }
        }
        
    except Exception as e:
        print(f"ERROR in portfolio calculation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise e  # Re-raise to see the full error

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)