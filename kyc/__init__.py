"""
KYC (Know Your Customer) Risk Assessment Module

This module handles customer risk profiling through scenario-based questions,
consistency validation, and mapping to portfolio optimization constraints.
"""

from .models import KYCResponse, RiskProfile, KYCInconsistency
from .risk_assessor import KYCRiskAssessor
from .constants import RISK_CATEGORIES, KYC_QUESTIONS

__all__ = [
    'KYCResponse',
    'RiskProfile', 
    'KYCInconsistency',
    'KYCRiskAssessor',
    'RISK_CATEGORIES',
    'KYC_QUESTIONS'
]