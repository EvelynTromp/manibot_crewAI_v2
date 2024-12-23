from crewai import Task
from typing import Dict
from utils.logger import get_logger
from pydantic import Field, BaseModel

logger = get_logger(__name__)

class AnalyzeOpportunityTask(Task):
    """
    Task for analyzing trading opportunities using GPT-4's search capabilities.
    This task now incorporates direct market research and analysis.
    """
    
    def __init__(self, market_id: str, agent):
        context_item = {
            "market_id": market_id,
            "description": f"Analyze trading opportunity for market {market_id}",
            "expected_output": "Trading decision analysis with validation"
        }
        
        super().__init__(
            description=f"""Analyze trading opportunity for market {market_id} using GPT-4's search capabilities.
            
            Your responsibilities include:
            1. Search for and analyze relevant market information
            2. Evaluate source credibility and information timeliness
            3. Calculate probability estimates based on findings
            4. Consider market dynamics and timing factors
            5. Determine optimal position sizes if warranted
            6. Validate trading decisions against current data
            
            Ensure all analysis includes source attribution and 
            confidence levels for probability estimates.""",
            agent=agent,
            expected_output="""A dictionary containing:
                - research_findings: Key information from searched sources
                - estimated_probability: Calculated probability of event
                - confidence_level: Confidence in the analysis
                - key_factors: List of major decision factors
                - bet_recommendation: Detailed betting parameters if opportunity exists
                - sources: List of sources consulted with credibility ratings
                - validation_results: Results of decision validation""",
            context=[context_item]
        )


class ExecuteTradeTask(Task):
    """
    Task for executing trades with enhanced market awareness and validation.
    """
    
    def __init__(self, market_id: str, agent):
        context_item = {
            "market_id": market_id,
            "description": f"Execute and monitor trade for market {market_id}",
            "expected_output": "Trade execution results with validation"
        }
        
        super().__init__(
            description=f"""Execute and monitor trade for market {market_id} with enhanced validation.
            
            Your responsibilities include:
            1. Verify current market conditions
            2. Validate trade parameters
            3. Execute trade with specified parameters
            4. Monitor execution success
            5. Record detailed trade information
            6. Track initial position performance
            
            Ensure all trades meet risk management criteria
            and include comprehensive validation checks.""",
            agent=agent,
            expected_output="""A dictionary containing:
                - success: Boolean indicating if trade was executed
                - trade_details: Complete trade parameters and results
                - execution_status: Current status of the trade
                - validation_results: Pre-trade validation details
                - position_metrics: Initial position tracking data
                - risk_metrics: Risk management calculations
                - error: Error details if unsuccessful""",
            context=[context_item]
        )

    async def execute(self, market_id: str, decision: Dict, analysis: Dict) -> Dict:
        """Execute the trading task with enhanced validation."""
        logger.info(f"Starting trade execution for market {market_id}")
        return await self.agent.execute_trade(market_id, decision, analysis)