from crews.base_crew import BaseCrew
from agents.roles.researcher import ResearcherAgent
from agents.roles.decision_maker import DecisionMakerAgent
from agents.roles.executor import ExecutorAgent
from tasks.task_definitions import (
    ResearchMarketTask,
    AnalyzeOpportunityTask,
    ExecuteTradeTask
)
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class MarketCrew(BaseCrew):
    """Crew for coordinating market research, analysis, and trading."""
    
    def __init__(self):
        # Create our agents
        researcher = ResearcherAgent()
        decision_maker = DecisionMakerAgent()
        executor = ExecutorAgent()
        
        # Initialize with our agents and empty tasks list
        super().__init__(
            agents=[researcher, decision_maker, executor],
            tasks=[],
            verbose=True
        )
    
    async def analyze_and_trade(self, market_id: str) -> Dict:
        """
        Coordinate the full analysis and trading process for a market.
        
        Args:
            market_id: ID of the market to analyze
            
        Returns:
            Dictionary containing process results
        """
        try:
            # Set up tasks for this market
            self._setup_market_tasks(market_id)
            
            # Get agents by role
            researcher = next((a for a in self.agents if a.role == 'Market Researcher'), None)
            decision_maker = next((a for a in self.agents if a.role == 'Market Decision Maker'), None)
            executor = next((a for a in self.agents if a.role == 'Market Executor'), None)
            
            if not all([researcher, decision_maker, executor]):
                raise ValueError("Could not find all required agents")
            
            # Execute research
            research_data = await researcher.research_market(market_id)
            
            # Make decision
            analysis = await decision_maker.analyze_opportunity(research_data)
            
            # Execute trade if recommended
            result = {"market_id": market_id, "success": True}
            if analysis.get('bet_recommendation'):
                if await decision_maker.validate_decision(
                    research_data['market_data'],
                    analysis,
                    analysis['bet_recommendation']
                ):
                    execution_result = await executor.execute_trade(
                        market_id,
                        analysis,
                        research_data
                    )
                    result.update(execution_result)
                else:
                    result.update({"success": False, "reason": "Failed validation"})
            else:
                result.update({"success": False, "reason": "No trading opportunity"})
            
            # Log execution
            self.log_execution({
                "market_id": market_id,
                "research_data": research_data,
                "analysis": analysis,
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in market crew execution: {str(e)}")
            await self.handle_error(e, {"market_id": market_id})
            return {"success": False, "error": str(e)}
    
    async def scan_markets(self, limit: int = 3) -> List[Dict]:
        """
        Scan for trading opportunities across multiple markets.
        
        Args:
            limit: Maximum number of markets to analyze
            
        Returns:
            List of analysis results for each market
        """
        try:
            researcher = next((a for a in self.agents if a.role == 'Market Researcher'), None)
            if not researcher:
                raise ValueError("Could not find researcher agent")
                
            logger.info(f"Starting market scan. Will analyze up to {limit} markets")
            active_markets = await researcher.get_active_markets(limit)
            logger.info(f"Found {len(active_markets)} markets to analyze")

            results = []
            for market in active_markets:
                result = await self.analyze_and_trade(market['id'])
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error scanning markets: {str(e)}")
            return []
    
    async def monitor_positions(self) -> List[Dict]:
        """Monitor all active positions."""
        executor = next((a for a in self.agents if a.role == 'Market Executor'), None)
        if not executor:
            raise ValueError("Could not find executor agent")
        return await executor.monitor_positions()
    
    def _setup_market_tasks(self, market_id: str):
        """Set up tasks for analyzing a specific market."""
        researcher = next((a for a in self.agents if a.role == 'Market Researcher'), None)
        decision_maker = next((a for a in self.agents if a.role == 'Market Decision Maker'), None)
        executor = next((a for a in self.agents if a.role == 'Market Executor'), None)
        
        if not all([researcher, decision_maker, executor]):
            raise ValueError("Could not find all required agents")
            
        self.tasks = [
            ResearchMarketTask(
                market_id=market_id,
                agent=researcher
            ),
            AnalyzeOpportunityTask(
                market_id=market_id,
                agent=decision_maker
            ),
            ExecuteTradeTask(
                market_id=market_id,
                agent=executor
            )
        ]