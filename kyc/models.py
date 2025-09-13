"""
Data models for KYC risk assessment system.

These models define the structure for KYC responses, risk profiles,
and validation results used throughout the assessment process.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class InconsistencyType(Enum):
    """Types of inconsistencies that can be detected in KYC responses"""
    SHORT_HORIZON_HIGH_RISK = "short_horizon_high_risk"
    INEXPERIENCED_AGGRESSIVE = "inexperienced_aggressive" 
    LOW_CAPACITY_HIGH_APPETITE = "low_capacity_high_appetite"
    SLEEP_LOSS_MISMATCH = "sleep_loss_mismatch"


@dataclass
class KYCResponse:
    """
    Raw responses from KYC questionnaire.
    Each score is 0-100 based on the answer selected.
    """
    horizon_score: int          # Investment time horizon (0-100)
    loss_tolerance: int         # Loss tolerance scenario (0-100)  
    experience_score: int       # Market experience and behavior (0-100)
    financial_score: int        # Financial capacity (0-100)
    goal_score: int            # Investment objectives (0-100)
    sleep_score: int           # Sleep-at-night test (0-100)
    
    def __post_init__(self):
        """Validate that all scores are in valid range"""
        for field_name, value in self.__dict__.items():
            if not isinstance(value, int) or not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be an integer between 0 and 100, got {value}")


@dataclass 
class KYCInconsistency:
    """Represents an inconsistency found in KYC responses"""
    type: InconsistencyType
    message_hebrew: str
    message_english: str
    suggested_action: str
    severity: str = "warning"  # "warning" or "error"


@dataclass
class RiskProfile:
    """
    Processed risk profile result from KYC assessment.
    
    This contains the final risk classification and metadata needed
    for portfolio optimization and user communication.
    """
    # Core classification
    risk_level: int             # 1-10 scale for portfolio optimizer
    category_hebrew: str        # Hebrew risk category name
    category_english: str       # English risk category name  
    composite_score: float      # Raw weighted score before mapping
    
    # Risk measures for constraints
    max_drawdown: float         # Maximum acceptable portfolio drawdown
    target_volatility: float    # Target annual volatility  
    recovery_time_months: int   # Maximum acceptable recovery time
    
    # Portfolio allocation guidelines
    equity_range: tuple         # (min, max) equity allocation
    international_max: float    # Maximum international exposure
    alternatives_max: float     # Maximum alternative investments
    
    # Assessment metadata
    inconsistencies: List[KYCInconsistency]
    confidence_score: float     # 0-1 confidence in assessment
    assessment_timestamp: Optional[str] = None
    
    def is_consistent(self) -> bool:
        """Check if profile has any error-level inconsistencies"""
        return not any(inc.severity == "error" for inc in self.inconsistencies)
    
    def has_warnings(self) -> bool:
        """Check if profile has any warnings"""
        return len(self.inconsistencies) > 0