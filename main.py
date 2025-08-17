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
    # TODO: Implement portfolio optimization logic
    return {
        "risk_level": risk_level,
        "investment_amount": investment_amount,
        "portfolio": {
            "US_Stocks": 0.6,
            "International_Stocks": 0.2,
            "Bonds": 0.15,
            "Commodities": 0.05
        },
        "expected_return": 7.2,
        "volatility": 12.5
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)