from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from content_loader import content_loader, LANGUAGES

app = FastAPI(title="Quantica", description="Intelligent Portfolio Optimization Platform")

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

def render_template(request: Request, template_name: str, context: dict = None):
    """Helper function to render templates with content support"""
    if context is None:
        context = {}
    
    # Get language and content context
    lang_context = content_loader.get_language_context(request)
    context.update(lang_context)
    
    # Add request to context
    context['request'] = request
    
    return templates.TemplateResponse(template_name, context)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/set-language")
async def set_language(request: Request, lang: str, redirect_to: str = "/"):
    """Set language preference and redirect"""
    response = HTMLResponse(content="<script>window.location.href='" + redirect_to + "';</script>")
    if lang in LANGUAGES:
        response.set_cookie(key="language", value=lang, max_age=30*24*60*60)  # 30 days
    return response

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render_template(request, "index.html")

@app.get("/risk-assessment", response_class=HTMLResponse)
async def risk_assessment(request: Request):
    return render_template(request, "risk_assessment.html")

@app.get("/methodology", response_class=HTMLResponse)
async def methodology(request: Request):
    return render_template(request, "methodology.html")

@app.get("/education", response_class=HTMLResponse)
async def education(request: Request):
    return render_template(request, "education.html")

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return render_template(request, "pricing.html")

@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    return render_template(request, "faq.html")

@app.get("/legal/disclaimers", response_class=HTMLResponse)
async def legal_disclaimers(request: Request):
    return render_template(request, "legal/disclaimers.html")

@app.get("/support", response_class=HTMLResponse)
async def support(request: Request):
    return render_template(request, "support.html")

@app.post("/api/calculate-portfolio")
async def calculate_portfolio(
    # KYC Responses (replacing risk_level)
    horizon_score: int = Form(...),
    loss_tolerance: int = Form(...), 
    experience_score: int = Form(...),
    financial_score: int = Form(...),
    goal_score: int = Form(...),
    sleep_score: int = Form(...),
    # Existing parameters
    investment_amount: float = Form(...),
    investment_duration: float = Form(10.0)
):
    import traceback
    
    try:
        # Process KYC responses first
        from kyc import KYCRiskAssessor
        
        kyc_responses = {
            'horizon_score': horizon_score,
            'loss_tolerance': loss_tolerance,
            'experience_score': experience_score,
            'financial_score': financial_score, 
            'goal_score': goal_score,
            'sleep_score': sleep_score
        }
        
        kyc_assessor = KYCRiskAssessor()
        kyc_result = kyc_assessor.process_responses(kyc_responses)
        
        print(f"KYC Assessment: {kyc_result.category_english}, risk_level={kyc_result.risk_level}")
        
        # Check for error-level inconsistencies (block portfolio calculation)
        if not kyc_result.is_consistent():
            error_inconsistencies = [inc for inc in kyc_result.inconsistencies if inc.severity == 'error']
            if error_inconsistencies:
                return {
                    "error": "inconsistent_responses",
                    "error_type": "blocking_inconsistencies", 
                    "kyc_profile": {
                        "category": kyc_result.category_english,
                        "inconsistencies": [
                            {
                                "type": inc.type.value,
                                "message": inc.message_english,
                                "severity": inc.severity
                            }
                            for inc in error_inconsistencies
                        ]
                    }
                }
        
        print(f"Starting optimization for risk level {kyc_result.risk_level}, amount ${investment_amount}, duration {investment_duration} years")
        
        from portfolio.optimizer_v2 import AdvancedPortfolioOptimizer
        from portfolio.data_manager import MarketDataManager
        from portfolio.analytics import PortfolioAnalytics
        
        # Initialize components
        data_manager = MarketDataManager()
        analytics = PortfolioAnalytics()
        optimizer = AdvancedPortfolioOptimizer(data_manager, analytics)
        
        # Optimize portfolio using KYC-derived risk level
        result = optimizer.optimize_portfolio(
            risk_level=kyc_result.risk_level,
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
            "risk_level": kyc_result.risk_level,
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
            },
            # NEW: KYC Profile Information
            "kyc_profile": {
                "category": kyc_result.category_english,
                "category_hebrew": kyc_result.category_hebrew,
                "composite_score": round(kyc_result.composite_score, 1),
                "confidence_score": round(kyc_result.confidence_score, 2),
                "risk_constraints": {
                    "max_drawdown": f"{kyc_result.max_drawdown:.1%}",
                    "target_volatility": f"{kyc_result.target_volatility:.1%}",
                    "recovery_time_months": kyc_result.recovery_time_months,
                    "equity_range": f"{kyc_result.equity_range[0]:.0%}-{kyc_result.equity_range[1]:.0%}",
                    "international_max": f"{kyc_result.international_max:.0%}",
                    "alternatives_max": f"{kyc_result.alternatives_max:.0%}"
                },
                "inconsistencies": [
                    {
                        "type": inc.type.value,
                        "message": inc.message_english,
                        "severity": inc.severity
                    }
                    for inc in kyc_result.inconsistencies
                ],
                "has_warnings": kyc_result.has_warnings()
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