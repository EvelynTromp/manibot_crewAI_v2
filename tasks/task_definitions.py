from crewai import Task
from typing import Dict
from utils.logger import get_logger
from pydantic import Field, BaseModel

logger = get_logger(__name__)

class ResearchMarketTask(Task):
    """Task for researching a specific market."""
    
    def __init__(self, market_id: str, agent):
        # Create properly structured context item
        context_item = {
            "market_id": market_id,
            "description": f"Research market {market_id} for trading opportunities",
            "expected_output": "Market research data and analysis"
        }
        
        super().__init__(
            description=f"""Research market {market_id}.
            1. Gather market details and current positions
            2. Search for relevant information
            3. Analyze market dynamics
            4. Prepare research summary""",
            agent=agent,
            expected_output="""A dictionary containing:
                - market_data: Current market information and statistics
                - research_findings: List of relevant information from searches
                - market_positions: Current market positions
                - summary: Comprehensive research summary""",
            context=[context_item]  # List with one properly structured dict
        )


class AnalyzeOpportunityTask(Task):
    """Task for analyzing trading opportunities."""
    
    def __init__(self, market_id: str, agent):
        # Create properly structured context item
        context_item = {
            "market_id": market_id,
            "description": f"Analyze trading opportunity for market {market_id}",
            "expected_output": "Trading decision analysis"
        }
        
        super().__init__(
            description=f"""Analyze trading opportunity for market {market_id}.
            1. Review research data
            2. Identify potential edges
            3. Calculate optimal position size
            4. Validate trading decision""",
            agent=agent,
            expected_output="""A dictionary containing:
                - estimated_probability: Calculated probability of event
                - key_factors: List of key decision factors
                - bet_recommendation: Detailed betting parameters if opportunity exists
                - confidence_level: Confidence in the analysis""",
            context=[context_item]  # List with one properly structured dict
        )


class ExecuteTradeTask(Task):
    """Task for executing trades."""
    
    def __init__(self, market_id: str, agent):
        # Create properly structured context item
        context_item = {
            "market_id": market_id,
            "description": f"Execute trade for market {market_id}",
            "expected_output": "Trade execution results"
        }
        
        super().__init__(
            description=f"""Execute trade for market {market_id}.
            1. Verify market conditions
            2. Place trade with specified parameters
            3. Record trade details
            4. Monitor execution status""",
            agent=agent,
            expected_output="""A dictionary containing:
                - success: Boolean indicating if trade was executed
                - trade: Trade details including ID and parameters if successful
                - error: Error details if unsuccessful""",
            context=[context_item]  # List with one properly structured dict
        )

    async def execute(self, market_id: str, decision: Dict, analysis: Dict) -> Dict:
        """Execute the trading task."""
        logger.info(f"Starting trade execution for market {market_id}")
        return await self.agent.execute_trade(market_id, decision, analysis)