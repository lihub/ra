"""
Core KYC risk assessment logic.

Processes customer responses, validates consistency, and generates
risk profiles for portfolio optimization.
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime

from .models import KYCResponse, RiskProfile, KYCInconsistency, InconsistencyType
from .constants import RISK_CATEGORIES, SCORING_WEIGHTS, CONSISTENCY_RULES

logger = logging.getLogger(__name__)


class KYCRiskAssessor:
    """
    Core risk assessment engine that processes KYC responses and generates
    risk profiles for portfolio optimization.
    
    This class handles:
    - Consistency validation of responses
    - Composite risk score calculation  
    - Risk category mapping
    - Portfolio constraint generation
    """
    
    def __init__(self):
        """Initialize the risk assessor with default configuration"""
        self.scoring_weights = SCORING_WEIGHTS.copy()
        self.consistency_rules = CONSISTENCY_RULES.copy()
        
    def process_responses(self, responses_dict: Dict[str, int]) -> RiskProfile:
        """
        Main entry point: Process KYC responses and return complete risk profile.
        
        Args:
            responses_dict: Dictionary with question responses (scores 0-100)
            
        Returns:
            RiskProfile: Complete risk assessment with constraints and metadata
            
        Raises:
            ValueError: If responses are invalid or missing required fields
        """
        logger.info("Processing KYC responses")
        
        # Validate and create response object
        kyc_response = self._validate_and_create_response(responses_dict)
        
        # Check for inconsistencies
        inconsistencies = self._validate_consistency(kyc_response)
        
        # Calculate composite risk score
        composite_score = self._calculate_composite_score(kyc_response)
        
        # Apply consistency adjustments
        adjusted_score = self._apply_consistency_adjustments(
            composite_score, kyc_response, inconsistencies
        )
        
        # Map to risk category and level
        risk_category, risk_level = self._map_to_risk_category(adjusted_score)
        
        # Generate risk profile
        risk_profile = self._create_risk_profile(
            risk_level=risk_level,
            category=risk_category, 
            composite_score=adjusted_score,
            inconsistencies=inconsistencies,
            original_response=kyc_response
        )
        
        logger.info(f"KYC assessment complete: risk_level={risk_level}, category={risk_category}")
        return risk_profile
    
    def _validate_and_create_response(self, responses_dict: Dict[str, int]) -> KYCResponse:
        """Validate input and create KYCResponse object"""
        required_fields = ['horizon_score', 'loss_tolerance', 'experience_score', 
                          'financial_score', 'goal_score', 'sleep_score']
        
        for field in required_fields:
            if field not in responses_dict:
                raise ValueError(f"Missing required field: {field}")
        
        try:
            return KYCResponse(**responses_dict)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid KYC responses: {e}")
    
    def _validate_consistency(self, response: KYCResponse) -> List[KYCInconsistency]:
        """
        Check for inconsistencies in KYC responses using predefined rules.
        
        Args:
            response: Validated KYC response object
            
        Returns:
            List of inconsistencies found
        """
        inconsistencies = []
        
        for inconsistency_type, rule in self.consistency_rules.items():
            if rule['condition'](response):
                inconsistency = KYCInconsistency(
                    type=inconsistency_type,
                    message_hebrew=rule['message_he'],
                    message_english=rule['message_en'],
                    suggested_action=rule['suggested_action'],
                    severity=rule['severity']
                )
                inconsistencies.append(inconsistency)
                
                logger.warning(f"Inconsistency detected: {inconsistency_type.value}")
        
        return inconsistencies
    
    def _calculate_composite_score(self, response: KYCResponse) -> float:
        """
        Calculate weighted composite risk score from individual responses.
        
        Args:
            response: KYC response object
            
        Returns:
            Composite score (0-100)
        """
        # Extract scores (excluding sleep_test which is used for validation only)
        scores = {
            'horizon': response.horizon_score,
            'loss_tolerance': response.loss_tolerance,
            'experience': response.experience_score, 
            'financial': response.financial_score,
            'goal': response.goal_score
        }
        
        # Calculate weighted average
        composite_score = sum(
            scores[component] * self.scoring_weights[component]
            for component in scores.keys()
        )
        
        logger.debug(f"Composite score calculated: {composite_score}")
        return composite_score
    
    def _apply_consistency_adjustments(self, 
                                    composite_score: float,
                                    response: KYCResponse,
                                    inconsistencies: List[KYCInconsistency]) -> float:
        """
        Apply score adjustments based on detected inconsistencies.
        
        Args:
            composite_score: Original calculated score
            response: Original response for reference
            inconsistencies: List of detected inconsistencies
            
        Returns:
            Adjusted composite score
        """
        adjusted_score = composite_score
        
        for inconsistency in inconsistencies:
            action = inconsistency.suggested_action
            
            if action == 'reduce_risk_score':
                adjusted_score *= 0.8
                logger.info(f"Reducing risk score by 20% due to {inconsistency.type.value}")
                
            elif action == 'cap_at_moderate':
                adjusted_score = min(adjusted_score, 65)
                logger.info(f"Capping score at moderate due to {inconsistency.type.value}")
                
            elif action == 'reduce_to_conservative':
                adjusted_score = min(adjusted_score, 45)
                logger.info(f"Reducing to conservative due to {inconsistency.type.value}")
                
            elif action == 'use_conservative_score':
                # Use the more conservative of sleep test vs loss tolerance
                conservative_score = min(response.sleep_score, response.loss_tolerance)
                # Recalculate composite with conservative loss tolerance
                adjusted_loss = conservative_score
                adjusted_composite = (
                    response.horizon_score * self.scoring_weights['horizon'] +
                    adjusted_loss * self.scoring_weights['loss_tolerance'] +
                    response.experience_score * self.scoring_weights['experience'] +
                    response.financial_score * self.scoring_weights['financial'] +
                    response.goal_score * self.scoring_weights['goal']
                )
                adjusted_score = adjusted_composite
                logger.info(f"Using conservative score due to sleep/loss mismatch")
        
        return max(0, min(100, adjusted_score))  # Ensure bounds
    
    def _map_to_risk_category(self, composite_score: float) -> Tuple[str, int]:
        """
        Map composite score to risk category and level.
        
        Args:
            composite_score: Adjusted composite score (0-100)
            
        Returns:
            Tuple of (category_key, risk_level_1_to_10)
        """
        # Find matching category
        for category_key, category_data in RISK_CATEGORIES.items():
            min_score, max_score = category_data['score_range']
            if min_score <= composite_score <= max_score:
                # Map to 1-10 scale for portfolio optimizer
                risk_level = self._score_to_risk_level(composite_score, min_score, max_score)
                return category_key, risk_level
        
        # Fallback (shouldn't happen with proper bounds)
        logger.warning(f"Score {composite_score} didn't match any category, defaulting to moderate")
        return 'מתון', 5
    
    def _score_to_risk_level(self, score: float, category_min: float, category_max: float) -> int:
        """
        Convert composite score to 1-10 risk level within category bounds.
        
        This ensures we use the full 1-10 range while respecting category constraints.
        """
        if score <= 25:
            return max(1, min(3, int(1 + (score / 25) * 2)))
        elif score <= 45:
            return max(3, min(5, int(3 + ((score - 25) / 20) * 2)))
        elif score <= 65:
            return max(5, min(7, int(5 + ((score - 45) / 20) * 2)))
        elif score <= 85:
            return max(7, min(9, int(7 + ((score - 65) / 20) * 2)))
        else:
            return max(9, min(10, int(9 + ((score - 85) / 15) * 1)))
    
    def _create_risk_profile(self,
                           risk_level: int,
                           category: str, 
                           composite_score: float,
                           inconsistencies: List[KYCInconsistency],
                           original_response: KYCResponse) -> RiskProfile:
        """
        Create complete risk profile with all metadata and constraints.
        
        Args:
            risk_level: Calculated risk level (1-10)
            category: Risk category key
            composite_score: Final adjusted composite score
            inconsistencies: Any inconsistencies found
            original_response: Original KYC response
            
        Returns:
            Complete RiskProfile object
        """
        category_data = RISK_CATEGORIES[category]
        
        # Calculate confidence score based on inconsistencies
        confidence = 1.0 - (len([i for i in inconsistencies if i.severity == 'warning']) * 0.1)
        confidence = max(0.5, confidence)  # Minimum 50% confidence
        
        return RiskProfile(
            # Core classification
            risk_level=risk_level,
            category_hebrew=category,
            category_english=category_data['name_en'],
            composite_score=composite_score,
            
            # Risk measures
            max_drawdown=category_data['max_drawdown'],
            target_volatility=category_data['target_volatility'],
            recovery_time_months=category_data['recovery_time_months'],
            
            # Portfolio constraints  
            equity_range=category_data['equity_range'],
            international_max=category_data['international_max'],
            alternatives_max=category_data['alternatives_max'],
            
            # Metadata
            inconsistencies=inconsistencies,
            confidence_score=confidence,
            assessment_timestamp=datetime.now().isoformat()
        )