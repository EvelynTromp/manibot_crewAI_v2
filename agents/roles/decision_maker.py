from crewai import Agent
from typing import Dict, Optional
from core.gpt_client import GPTClient
from config.settings import settings

class DecisionMakerAgent(Agent):
    """Agent responsible for analyzing opportunities and making trading decisions."""

    def __init__(self):
        # Initialize base Agent first
        super().__init__(
            role='Market Decision Maker',
            goal='Analyze research data and make optimal trading decisions',
            backstory="""You are an experienced decision maker with expertise in 
            prediction markets. Your strength lies in analyzing complex information 
            and making calculated betting decisions based on probability theory 
            and market dynamics.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Initialize instance variable without direct assignment
        self._gpt_client = None

    @property
    def gpt_client(self):
        """Lazy initialization of GPT client."""
        if self._gpt_client is None:
            self._gpt_client = GPTClient()
        return self._gpt_client

    # async def analyze_opportunity(self, research_data: Dict) -> Dict:
    #     """
    #     Analyze market research and determine if there's a trading opportunity.
        
    #     Args:
    #         research_data: Dictionary containing market and research information
            
    #     Returns:
    #         Dictionary containing analysis and trading recommendation
    #     """
    #     # Analyze market using GPT
    #     analysis = await self.gpt_client.analyze_market(
    #         research_data['market_data'],
    #         research_data['summary']
    #     )
        
    #     # Determine optimal bet size if opportunity exists
    #     if analysis['estimated_probability'] is not None:
    #         bet_recommendation = self._calculate_bet_size(
    #             analysis['estimated_probability'],
    #             analysis['confidence_level'],
    #             research_data['market_data']
    #         )
    #         analysis['bet_recommendation'] = bet_recommendation
        
    #     return analysis

    # In decision_maker.py, modify the analyze_opportunity method
    async def analyze_opportunity(self, research_data: Dict) -> Dict:
        """
        Modified for testing: Always recommends a small trade
        
        Args:
            research_data: Dictionary containing market and research information
            
        Returns:
            Dictionary containing analysis and trading recommendation
        """
        # Get the current market probability
        market_prob = float(research_data['market_data'].get('probability', 0.5))
        
        # For testing: Always generate a recommendation
        analysis = {
            'estimated_probability': market_prob + 0.05,  # Slightly higher than market
            'confidence_level': 0.8,  # High confidence for testing
            'key_factors': ['Test factor 1', 'Test factor 2'],
            'bet_recommendation': {
                'amount': 5.0,  # Small fixed bet size for testing
                'probability': market_prob + 0.05,
                'edge': 0.05,
                'confidence': 0.8,
                'market_quality_score': 1.0
            }
        }
        
        return analysis




    def _calculate_bet_size(self, 
                          estimated_prob: float, 
                          confidence: float, 
                          market_data: Dict) -> Optional[Dict]:
        """Calculate optimal bet size based on edge and confidence."""
        market_prob = float(market_data.get('probability', 0))
        
        # Calculate edge (difference between our estimate and market probability)
        edge = abs(estimated_prob - market_prob)
        
        # Adjust minimum edge based on market metrics
        base_min_edge = 0.03  # Reduced from 0.05 for pre-qualified markets
        
        # Adjust required edge based on market quality metrics
        metrics = market_data.get('metrics', {})
        min_edge = base_min_edge
        
        if metrics:
            # Reduce required edge for high-quality markets
            if (len(market_data.get('traders', [])) >= 5 and 
                float(market_data.get('totalLiquidity', 0)) >= 50):
                min_edge *= 0.8  # 20% reduction in required edge
        
        # Only bet if we have a significant edge
        if edge < min_edge:
            return None
        
        # Calculate base bet size based on edge and confidence
        base_bet = settings.MIN_BET_AMOUNT + (
            (settings.MAX_BET_AMOUNT - settings.MIN_BET_AMOUNT) * 
            edge * confidence
        )
        
        # Adjust max bet ratio based on market quality
        default_max_ratio = 0.15  # Increased from 0.10 for pre-qualified markets
        max_bet_ratio = default_max_ratio
        
        if metrics:
            # Allow larger bets for more liquid markets
            if float(market_data.get('totalLiquidity', 0)) >= 100:
                max_bet_ratio = 0.20
        
        # Calculate maximum bet based on liquidity
        liquidity = float(market_data.get('totalLiquidity', 0))
        max_bet = liquidity * max_bet_ratio
        
        bet_amount = min(base_bet, max_bet)
        
        return {
            'amount': round(bet_amount, 2),
            'probability': estimated_prob,
            'edge': edge,
            'confidence': confidence,
            'market_quality_score': self._calculate_market_quality_score(market_data)
        }

    def _calculate_market_quality_score(self, market_data: Dict) -> float:
        """Calculate a quality score for the market based on key metrics."""
        base_score = 0.0
        
        # Add points for each positive market characteristic
        if len(market_data.get('traders', [])) >= 5:
            base_score += 0.2
        
        if float(market_data.get('totalLiquidity', 0)) >= 50:
            base_score += 0.2
            
        if float(market_data.get('volume', 0)) >= 10:
            base_score += 0.2
            
        metrics = market_data.get('metrics', {})
        if metrics.get('liquidity_per_trader', 0) >= 10:
            base_score += 0.2
            
        if metrics.get('trades_per_trader', 0) >= 2:
            base_score += 0.2
            
        return min(base_score, 1.0)

    # async def validate_decision(self, 
    #                           market_data: Dict, 
    #                           analysis: Dict, 
    #                           bet_details: Dict) -> bool:
    #     """
    #     Validate the trading decision before execution.
        
    #     Args:
    #         market_data: Market information
    #         analysis: Market analysis
    #         bet_details: Proposed bet details
            
    #     Returns:
    #         Boolean indicating whether to proceed with the bet
    #     """
    #     # Basic validation checks
    #     if not self._validate_bet_constraints(bet_details):
    #         return False
        
    #     # Use GPT for additional validation
    #     return await self.gpt_client.validate_decision(
    #         market_data,
    #         analysis,
    #         bet_details
    #     )

    # Also in decision_maker.py, modify the validate_decision method
    async def validate_decision(self, 
                            market_data: Dict, 
                            analysis: Dict, 
                            bet_details: Dict) -> bool:
        """
        Modified for testing: Always validates the trade
        """
        return True

    def _validate_bet_constraints(self, bet_details: Dict) -> bool:
        """Validate that bet meets basic constraints."""
        if not bet_details:
            return False
            
        amount = bet_details.get('amount', 0)
        probability = bet_details.get('probability', 0)
        
        # Check amount constraints
        if not (settings.MIN_BET_AMOUNT <= amount <= settings.MAX_BET_AMOUNT):
            return False
            
        # Check probability constraints
        if not (settings.MIN_PROBABILITY <= probability <= settings.MAX_PROBABILITY):
            return False
            
        return True

    def get_decision_explanation(self, analysis: Dict) -> str:
        """Generate a human-readable explanation of the decision."""
        if not analysis.get('bet_recommendation'):
            return "No betting opportunity identified based on current analysis."
            
        explanation = f"""
        Decision Analysis:
        - Estimated probability: {analysis['estimated_probability']:.1%}
        - Confidence level: {analysis['confidence_level']:.1%}
        - Recommended bet: ${analysis['bet_recommendation']['amount']}
        - Expected edge: {analysis['bet_recommendation']['edge']:.1%}
        
        Key factors considered:
        """
        
        for factor in analysis.get('key_factors', []):
            explanation += f"- {factor}\n"
            
        return explanation