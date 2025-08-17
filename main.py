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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/risk-assessment", response_class=HTMLResponse)
async def risk_assessment(request: Request):
    return templates.TemplateResponse("risk_assessment.html", {"request": request})

@app.post("/api/calculate-portfolio")
async def calculate_portfolio(
    risk_level: int = Form(...),
    investment_amount: float = Form(...)
):
    from portfolio.optimizer import PortfolioOptimizer
    import traceback
    
    try:
        print(f"Starting optimization for risk level {risk_level}, amount ${investment_amount}")
        
        optimizer = PortfolioOptimizer()
        result = optimizer.optimize_portfolio(risk_level=risk_level)
        
        print(f"Optimization completed successfully: {result['optimization_success']}")
        
        # Convert allocation percentages to dollar amounts
        portfolio_dollars = {}
        for asset, weight in result['allocation'].items():
            portfolio_dollars[asset] = round(investment_amount * weight, 2)
        
        return {
            "risk_level": risk_level,
            "investment_amount": investment_amount,
            "portfolio": result['allocation'],
            "portfolio_dollars": portfolio_dollars,
            "expected_return": result['expected_return'] * 100,  # Convert to percentage
            "volatility": result['volatility'] * 100,  # Convert to percentage
            "sharpe_ratio": result['sharpe_ratio'],
            "optimization_success": result['optimization_success'],
            "performance_history": result['performance_history']
        }
        
    except Exception as e:
        print(f"ERROR in portfolio calculation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise e  # Re-raise to see the full error

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)