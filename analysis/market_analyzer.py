# analysis/market_analyzer.py

from typing import Dict, Optional
from datetime import datetime
from config.settings import settings
from core.gpt_client import GPTClient
from utils.logger import get_logger
import logging
import json

logger = get_logger(__name__)

class MarketAnalyzer:
    """A dedicated system for analyzing prediction markets."""
    
  
    def __init__(self, manifold_client=None):
        """Initialize the market analyzer with required clients."""
        self.gpt_client = GPTClient(api_key=settings.OPENAI_API_KEY)
        self.manifold_client = manifold_client  # Accept manifold client as parameter
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        
    async def analyze_market(self, market_data: Dict) -> Dict:
        """Analyze a market with enhanced validation and edge detection."""
        try:
            # if market_data.get('outcomeType') != 'BINARY':
            #     return self._create_error_response("Non-binary market type")
            
            # First verify we can actually make a trade
            me_data = await self.manifold_client._make_request("GET", "me")
            balance = float(me_data.get('balance', 0))
            username = me_data.get('username', 'Unknown')
            user_id = me_data.get('id', 'Unknown')
            
            # logger.info(f"Analyzing market with account {username} (ID: {user_id})")
            # logger.info(f"Current balance: M${balance}")
            
            if balance < settings.MIN_BET_AMOUNT:
                msg = f"Insufficient balance (M${balance}) for minimum bet (M${settings.MIN_BET_AMOUNT})"
                logger.warning(f"Account {username} - {msg}")
                return self._create_error_response(msg)

            # First get the GPT analysis
            analysis = await self.gpt_client.analyze_market(market_data)
            
            # Early return if there's an error
            if analysis.get('error'):
                self.logger.warning(f"Analysis returned error: {analysis['error']}")
                return analysis

            # Extract probability and confidence
            est_prob = analysis.get('estimated_probability')
            confidence = analysis.get('confidence_level')
            
            # Validate the values
            if est_prob is None or confidence is None:
                return self._create_error_response("Missing probability or confidence values")
                
            if not (0 <= est_prob <= 1) or not (0 <= confidence <= 1):
                return self._create_error_response("Invalid probability or confidence range")

            # Get market probability, with proper error handling
            try:
                market_prob = float(market_data.get('probability', 0.5))
            except (TypeError, ValueError):
                market_prob = 0.5  # Default to 0.5 if we can't get a valid probability
            
            # Calculate edge
            edge = abs(est_prob - market_prob)
            self.logger.info(f"Edge calculated: {edge:.2%}")
            
            # Only create bet recommendation if edge is significant
            if edge >= settings.MIN_EDGE_REQUIREMENT:
                # Calculate bet amount based on edge and confidence
                bet_amount = self._calculate_position_size(edge, confidence)


                ##print("bet amount AAAAAAAAAAAAAAAA"  + str(bet_amount))
                
                analysis['bet_recommendation'] = {
                    'amount': bet_amount,
                    'probability': est_prob,
                    'direction': 'YES' if est_prob > market_prob else 'NO'
                }
                
                self.logger.info(
                    f"Trade opportunity found - "
                    f"Edge: {edge:.2%}, "
                    f"Direction: {analysis['bet_recommendation']['direction']}, "
                    f"Amount: ${bet_amount}"
                )
            else:
                self.logger.info(
                    f"No significant edge found - "
                    f"Edge: {edge:.2%}, "
                    f"Min Required: {settings.MIN_EDGE_REQUIREMENT:.2%}"
                )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing market: {str(e)}")
            return self._create_error_response(str(e))
        
    def _calculate_position_size(self, edge: float, confidence: float) -> float:
        """
        Calculates the optimal position size based on edge and confidence.
        Returns a bet amount between MIN_BET_AMOUNT and MAX_BET_AMOUNT.
        """
        try:
            # Get trade limits from settings
            min_bet = float(settings.MIN_BET_AMOUNT)
            max_bet = float(settings.MAX_BET_AMOUNT)
            
            # Scale bet size based on edge and confidence
            edge_factor = min(edge * 10, 1.0)  # Scale edge to max of 1.0
            confidence_factor = confidence
            
            # Calculate base bet size
            bet_size = min_bet + (max_bet - min_bet) * edge_factor * confidence_factor
            
            # Round to 2 decimal places and ensure within limits
            return round(min(max(bet_size, min_bet), max_bet), 2)
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return float(settings.MIN_BET_AMOUNT)  # Default to minimum bet on error
        

    def _create_error_response(self, error_msg: str) -> Dict:
        """Creates a standardized error response."""
        return {
            'success': False,
            'error': error_msg,
            'estimated_probability': None,
            'confidence_level': None,
            'reasoning': f"Analysis failed: {error_msg}",
            'key_factors': [],
            'bet_recommendation': None
        }
        
    def _validate_probability_and_confidence(self, analysis: Dict) -> bool:
        """
        Validates that probability and confidence values are present and within valid ranges.
        Returns True if valid, False otherwise.
        """
        try:
            # Check if values exist
            prob = analysis.get('estimated_probability')
            conf = analysis.get('confidence_level')
            
            if prob is None or conf is None:
                self.logger.warning("Missing probability or confidence values")
                return False
                
            # Validate ranges
            if not (0 <= prob <= 1) or not (0 <= conf <= 1):
                self.logger.warning(f"Invalid probability ({prob}) or confidence ({conf}) values")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error in probability validation: {str(e)}")
            return False

  
    def _create_error_response(self, error_msg: str) -> Dict:
        """Creates a standardized error response."""
        return {
            'success': False,
            'error': error_msg,
            'estimated_probability': None,
            'confidence_level': None,
            'reasoning': f"Analysis failed: {error_msg}",
            'key_factors': []
        }



    def _is_market_eligible(self, market_data: Dict) -> bool:
        """Determine if a market meets basic criteria for analysis."""
        try:
            requirements = settings.get_market_requirements()
            market_id = market_data.get('id', 'unknown')
            print(f"\nChecking market {market_id}:")
            
            # Check liquidity
            liquidity = float(market_data.get('totalLiquidity', 0))
            print(f"Liquidity: {liquidity} (min: {requirements['min_liquidity']})")
            if liquidity < requirements['min_liquidity']:
                return False
            
            # Check probability
            prob = float(market_data.get('probability', 0))
            print(f"Probability: {prob} (range: {requirements['min_probability']}-{requirements['max_probability']})")
            if not (requirements['min_probability'] <= prob <= requirements['max_probability']):
                return False
            
            print("Market passed all checks!")
            return True
            
        except Exception as e:
            print(f"Error checking eligibility: {str(e)}")
            return False
    
    def _validate_gpt_analysis(self, analysis: Dict) -> bool:
        """
        Validate that the GPT analysis contains all required information
        and that the values are within expected ranges.
        """
        required_fields = [
            'estimated_probability',
            'confidence_level',
            'reasoning',
            'key_factors'
        ]
        
        # Check all required fields exist
        if not all(field in analysis for field in required_fields):
            return False
            
        # Validate probability and confidence values
        prob = analysis['estimated_probability']
        conf = analysis['confidence_level']
        
        return (
            isinstance(prob, (int, float)) and
            isinstance(conf, (int, float)) and
            0 <= prob <= 1 and
            0 <= conf <= 1
        )
    
    def _evaluate_opportunity(self, analysis: Dict, market_data: Dict) -> Dict:
        """
        Evaluate if there's a trading opportunity based on the analysis.
        
        This method calculates the edge and determines if it's significant
        enough to warrant a trade.
        """
        market_prob = float(market_data.get('probability', 0))
        est_prob = analysis['estimated_probability']
        confidence = analysis['confidence_level']
        
        # Calculate edge (difference between our estimate and market probability)
        edge = abs(est_prob - market_prob)
        
        # Determine if edge is significant enough
        has_edge = edge >= settings.MIN_EDGE_REQUIREMENT
        
        return {
            'has_edge': has_edge,
            'edge': edge,
            'estimated_probability': est_prob,
            'market_probability': market_prob,
            'confidence': confidence,
            'direction': 'YES' if est_prob > market_prob else 'NO'
        }
    
    def _create_analysis_response(self, 
                                success: bool,
                                estimated_probability: Optional[float] = None,
                                confidence_level: Optional[float] = None,
                                reasoning: Optional[str] = None,
                                key_factors: Optional[list] = None,
                                bet_recommendation: Optional[Dict] = None,
                                opportunity_details: Optional[Dict] = None,
                                error: Optional[str] = None) -> Dict:
        """Create a standardized analysis response."""
        return {
            'success': success,
            'estimated_probability': estimated_probability,
            'confidence_level': confidence_level,
            'reasoning': reasoning,
            'key_factors': key_factors or [],
            'bet_recommendation': bet_recommendation,
            'opportunity_details': opportunity_details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }