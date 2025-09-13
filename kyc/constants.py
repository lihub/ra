"""
Constants and configuration for KYC risk assessment system.

Contains risk categories, question definitions, scoring weights,
and validation rules used throughout the assessment process.
"""

from typing import Dict, List, Tuple
from .models import InconsistencyType


# Risk Categories (refined based on our discussion)
RISK_CATEGORIES = {
    'שמרני_מאוד': {
        'score_range': (0, 25),
        'name_en': 'Ultra Conservative',
        'description_he': 'מתאים למשקיעים הרוצים בוודאות מרבית',
        'description_en': 'Suitable for investors seeking maximum certainty',
        
        # Key Risk Measures  
        'max_drawdown': 0.03,          # 3% maximum peak-to-trough loss
        'target_volatility': 0.04,     # 4% annual volatility
        'recovery_time_months': 6,      # 6 months to recover
        
        # Portfolio Constraints
        'equity_range': (0.05, 0.20),   # Very low equity exposure
        'international_max': 0.15,
        'alternatives_max': 0.02
    },
    
    'שמרני': {
        'score_range': (26, 45),
        'name_en': 'Conservative',
        'description_he': 'מתאים למשקיעים המעוניינים בצמיחה מתונה',
        'description_en': 'Suitable for investors seeking moderate growth',
        
        # Key Risk Measures
        'max_drawdown': 0.08,          # 8% maximum drawdown
        'target_volatility': 0.08,     # 8% annual volatility  
        'recovery_time_months': 12,     # 12 months recovery
        
        # Portfolio Constraints
        'equity_range': (0.15, 0.40),
        'international_max': 0.25,
        'alternatives_max': 0.05
    },
    
    'מתון': {
        'score_range': (46, 65),
        'name_en': 'Moderate',
        'description_he': 'איזון בין צמיחה לבטיחות',
        'description_en': 'Balance between growth and safety',
        
        # Key Risk Measures
        'max_drawdown': 0.15,          # 15% maximum drawdown
        'target_volatility': 0.12,     # 12% annual volatility
        'recovery_time_months': 24,     # 24 months recovery
        
        # Portfolio Constraints
        'equity_range': (0.30, 0.65),
        'international_max': 0.40,
        'alternatives_max': 0.10
    },
    
    'אגרסיבי': {
        'score_range': (66, 85),
        'name_en': 'Aggressive', 
        'description_he': 'מתאים למשקיעים המחפשים צמיחה גבוהה',
        'description_en': 'Suitable for investors seeking high growth',
        
        # Key Risk Measures
        'max_drawdown': 0.25,          # 25% maximum drawdown
        'target_volatility': 0.18,     # 18% annual volatility
        'recovery_time_months': 36,     # 36 months recovery
        
        # Portfolio Constraints
        'equity_range': (0.55, 0.80),
        'international_max': 0.60,
        'alternatives_max': 0.20
    },
    
    'אגרסיבי_מאוד': {
        'score_range': (86, 100),
        'name_en': 'Very Aggressive',
        'description_he': 'מקסום צמיחה עם נכונות לסיכון גבוה',
        'description_en': 'Maximum growth with high risk tolerance',
        
        # Key Risk Measures  
        'max_drawdown': 0.40,          # 40% maximum drawdown
        'target_volatility': 0.22,     # 22% annual volatility
        'recovery_time_months': 48,     # 48+ months recovery
        
        # Portfolio Constraints
        'equity_range': (0.70, 0.95),
        'international_max': 0.80,
        'alternatives_max': 0.30
    }
}


# KYC Questions with scoring (refined scenarios)
KYC_QUESTIONS = {
    'horizon': {
        'question_he': 'מתי אתה צפוי לזקוק לכסף המושקע?',
        'question_en': 'When do you expect to need the invested money?',
        'options': [
            {'text_he': 'תוך שנה אחת', 'text_en': 'Within 1 year', 'score': 0},
            {'text_he': '1-3 שנים', 'text_en': '1-3 years', 'score': 20},
            {'text_he': '4-7 שנים', 'text_en': '4-7 years', 'score': 50}, 
            {'text_he': '8-15 שנים', 'text_en': '8-15 years', 'score': 75},
            {'text_he': 'מעל 15 שנים', 'text_en': 'Over 15 years', 'score': 100}
        ]
    },
    
    'loss_tolerance': {
        'question_he': 'אם השקעה של 100,000 ש"ח תרד ל-75,000 ש"ח בתוך 6 חודשים, מה תעשה?',
        'question_en': 'If your ₪100,000 investment drops to ₪75,000 in 6 months, what would you do?',
        'options': [
            {'text_he': 'אמכור מיד כדי למנוע הפסדים נוספים', 'text_en': 'Sell immediately to prevent further losses', 'score': 0},
            {'text_he': 'אמכור חלק מההשקעה', 'text_en': 'Sell part of the investment', 'score': 25},
            {'text_he': 'אחכה ולא אעשה כלום', 'text_en': 'Wait and do nothing', 'score': 60},
            {'text_he': 'אקנה עוד בהזדמנות הזולה', 'text_en': 'Buy more at this discount', 'score': 100}
        ]
    },
    
    'experience': {
        'question_he': 'איך התנהגת במהלך קריסות השוק (2008, 2020)?',
        'question_en': 'How did you behave during market crashes (2008, 2020)?', 
        'options': [
            {'text_he': 'לא הייתי מושקע אז', 'text_en': 'I was not invested then', 'score': 20},
            {'text_he': 'מכרתי מחשש להפסדים', 'text_en': 'I sold due to fear of losses', 'score': 0},
            {'text_he': 'החזקתי את ההשקעות', 'text_en': 'I held my investments', 'score': 70},
            {'text_he': 'קניתי עוד כשהמחירים ירדו', 'text_en': 'I bought more when prices fell', 'score': 100}
        ]
    },
    
    'financial': {
        'question_he': 'כמה מהכנסתך החודשית אתה יכול להשקיע מבלי לפגוע ברמת חייך?',
        'question_en': 'How much of your monthly income can you invest without affecting your lifestyle?',
        'options': [
            {'text_he': 'עד 5%', 'text_en': 'Up to 5%', 'score': 20},
            {'text_he': '5-15%', 'text_en': '5-15%', 'score': 50},
            {'text_he': '15-25%', 'text_en': '15-25%', 'score': 75},
            {'text_he': 'מעל 25%', 'text_en': 'Over 25%', 'score': 100}
        ]
    },
    
    'goal': {
        'question_he': 'מה המטרה העיקרית של ההשקעה?',
        'question_en': 'What is the main goal of this investment?',
        'options': [
            {'text_he': 'שמירה על הקרן', 'text_en': 'Capital preservation', 'score': 0},
            {'text_he': 'הכנסה שוטפת', 'text_en': 'Current income', 'score': 25}, 
            {'text_he': 'צמיחה מתונה', 'text_en': 'Moderate growth', 'score': 60},
            {'text_he': 'צמיחה מקסימלית', 'text_en': 'Maximum growth', 'score': 100}
        ]
    },
    
    'sleep_test': {
        'question_he': 'איזה ירידה בתיק ההשקעות לא תיתן לך לישון בלילה?',
        'question_en': 'What portfolio decline would keep you awake at night?',
        'options': [
            {'text_he': 'מעל 5%', 'text_en': 'Over 5%', 'score': 0},
            {'text_he': 'מעל 15%', 'text_en': 'Over 15%', 'score': 30},
            {'text_he': 'מעל 25%', 'text_en': 'Over 25%', 'score': 70},
            {'text_he': 'מעל 40%', 'text_en': 'Over 40%', 'score': 100}
        ]
    }
}


# Scoring weights for composite calculation
SCORING_WEIGHTS = {
    'horizon': 0.25,        # 25% - Time horizon is crucial
    'loss_tolerance': 0.30, # 30% - Most important for risk tolerance  
    'experience': 0.20,     # 20% - Past behavior predicts future
    'financial': 0.15,      # 15% - Capacity to take risk
    'goal': 0.10           # 10% - Objectives matter but less critical
    # sleep_test is used for validation, not scoring
}


# Consistency validation rules
CONSISTENCY_RULES = {
    InconsistencyType.SHORT_HORIZON_HIGH_RISK: {
        'condition': lambda resp: resp.horizon_score < 30 and resp.loss_tolerance > 70,
        'message_he': 'השקעה לטווח קצר עם נכונות לסיכון גבוה - שקול גישה שמרנית יותר',
        'message_en': 'Short-term investment with high risk tolerance - consider a more conservative approach',
        'suggested_action': 'reduce_risk_score',
        'severity': 'warning'
    },
    
    InconsistencyType.INEXPERIENCED_AGGRESSIVE: {
        'condition': lambda resp: resp.experience_score < 30 and resp.goal_score > 80,
        'message_he': 'חוסר ניסיון עם יעדי צמיחה אגרסיביים - מומלץ להתחיל בגישה מתונה',
        'message_en': 'Inexperienced with aggressive growth goals - recommend starting with moderate approach',
        'suggested_action': 'cap_at_moderate',
        'severity': 'warning'
    },
    
    InconsistencyType.LOW_CAPACITY_HIGH_APPETITE: {
        'condition': lambda resp: resp.financial_score < 40 and resp.loss_tolerance > 60,
        'message_he': 'יכולת פיננסית נמוכה עם רצון לסיכון גבוה - חשוב להתחיל בשמרנות',
        'message_en': 'Low financial capacity with high risk appetite - important to start conservatively',
        'suggested_action': 'reduce_to_conservative',
        'severity': 'error'  # Block portfolio calculation
    },
    
    InconsistencyType.SLEEP_LOSS_MISMATCH: {
        'condition': lambda resp: abs(resp.sleep_score - resp.loss_tolerance) > 40,
        'message_he': 'סתירה בין סבילות הפסד מוצהרת למעשית - נשתמש בגבול השמרני יותר',
        'message_en': 'Contradiction between stated and practical loss tolerance - using the more conservative limit',
        'suggested_action': 'use_conservative_score',
        'severity': 'warning'
    }
}