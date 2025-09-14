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

def get_category_breakdown(allocation_percentages, data_manager):
    """Helper function to calculate category breakdown"""
    category_breakdown = {}
    
    for asset_name, weight in allocation_percentages.items():
        metadata = data_manager.asset_metadata.get(asset_name)
        if metadata:
            category = metadata.category
            if category not in category_breakdown:
                category_breakdown[category] = 0
            category_breakdown[category] += weight
    
    # Convert to percentages and round
    return {cat: round(weight * 100, 1) for cat, weight in category_breakdown.items()}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/reload-content")
async def reload_content():
    """Development endpoint to reload content files"""
    try:
        content_loader.reload_content()
        return {"status": "success", "message": "Content reloaded successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
        
        print(f"Starting optimization for {kyc_result.category_english} (score: {kyc_result.composite_score:.1f})")
        print(f"Investment: ₪{investment_amount:,.0f}, Duration: {investment_duration} years")
        
        from portfolio.sortino_adapter import SortinoPortfolioOptimizer
        
        # Initialize Sortino optimizer (better performance for aggressive investors)
        optimizer = SortinoPortfolioOptimizer()
        
        # Optimize portfolio using complete KYC response
        result = optimizer.optimize_portfolio(
            kyc_response=kyc_result,
            investment_amount=investment_amount,
            investment_duration_years=investment_duration
        )
        
        print(f"Optimization completed: {result.optimization_success} ({result.optimization_time_ms:.0f}ms)")
        print(f"Expected return: {result.expected_return_annual:.1%}, Volatility: {result.volatility_annual:.1%}")
        print(f"CVaR 95%: {result.cvar_95:.1%}, Max Drawdown: {result.max_drawdown:.1%}")
        
        return {
            "risk_assessment": {
                "category": kyc_result.category_english,
                "category_hebrew": kyc_result.category_hebrew,
                "composite_score": kyc_result.composite_score,
                "risk_level": kyc_result.risk_level
            },
            "investment_details": {
                "amount_ils": investment_amount,
                "duration_years": investment_duration,
                "currency": result.currency
            },
            "portfolio_allocation": {
                "percentages": result.allocation_percentages,
                "amounts_ils": result.allocation_ils_amounts,
                "total_invested": result.total_investment_ils
            },
            "performance_metrics": {
                "expected_return_annual": round(result.expected_return_annual * 100, 2),
                "volatility_annual": round(result.volatility_annual * 100, 2),
                "sharpe_ratio": round(result.sharpe_ratio, 2),
                "cvar_95": round(result.cvar_95 * 100, 2),
                "max_drawdown": round(result.max_drawdown * 100, 2),
                "risk_free_rate": round(result.risk_free_rate_used * 100, 2),
                "concentration_hhi": round(result.concentration_hhi, 3)
            },
            "risk_analysis": {
                "risk_contributions": result.risk_contributions,
                "category_breakdown": get_category_breakdown(result.allocation_percentages, optimizer.data_manager)
            },
            "optimization_info": {
                "success": result.optimization_success,
                "time_ms": round(result.optimization_time_ms, 1),
                "risk_category": result.risk_category
            },
            "kyc_inconsistencies": [
                {
                    "type": inc.type.value,
                    "message": inc.message_english,
                    "severity": inc.severity
                }
                for inc in kyc_result.inconsistencies
            ] if kyc_result.inconsistencies else []
        }
        
    except Exception as e:
        print(f"ERROR in portfolio calculation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise e  # Re-raise to see the full error

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)