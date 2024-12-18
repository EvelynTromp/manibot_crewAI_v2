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
    """Crew for coordinating market research, analysis, and trading with enhanced reporting."""
    
    def __init__(self):
        # Create our specialized agents
        researcher = ResearcherAgent()
        decision_maker = DecisionMakerAgent()
        executor = ExecutorAgent()
        
        # Initialize with our agents and empty tasks list
        super().__init__(
            agents=[researcher, decision_maker, executor],
            tasks=[],
            verbose=True
        )
        
        logger.info("Market crew initialized with enhanced reporting capabilities")

    async def scan_markets(self, limit: int = 1) -> List[Dict]: #  limit here sets how many markets will be analyzed during a single scan
        """Scan for trading opportunities across multiple markets with comprehensive reporting."""
        try:
            # Start new scan session
            self.start_scan_session()
            logger.info(f"Starting market scan. Will analyze up to {limit} markets")
            
            researcher = next((a for a in self.agents if a.role == 'Market Researcher'), None)
            if not researcher:
                raise ValueError("Could not find researcher agent")
            
            # Get markets to analyze
            active_markets = await researcher.get_active_markets(limit)
            logger.info(f"Found {len(active_markets)} markets to analyze")
            
            results = []
            for i, market in enumerate(active_markets, 1):
                logger.info(f"Analyzing market {i} of {len(active_markets)}")
                result = await self.analyze_and_trade(market['id'])
                results.append(result)
            
            # Finalize scan session and save consolidated report
            report_path = self.finalize_scan_session()
            logger.info(f"Scan complete. Full report saved to: {report_path}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error scanning markets: {str(e)}")
            return []

    async def analyze_and_trade(self, market_id: str) -> Dict:
        """Coordinate the full analysis and trading process with comprehensive reporting."""
        try:
            # Get our specialized agents
            researcher = next((a for a in self.agents if a.role == 'Market Researcher'), None)
            decision_maker = next((a for a in self.agents if a.role == 'Market Decision Maker'), None)
            executor = next((a for a in self.agents if a.role == 'Market Executor'), None)
            
            if not all([researcher, decision_maker, executor]):
                raise ValueError("Could not find all required agents")
            
            # Gather research data with enhanced error handling
            try:
                research_data = await researcher.research_market(market_id)
                logger.info(f"Research completed for market {market_id}")
            except Exception as e:
                logger.error(f"Research failed for market {market_id}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Research failed: {str(e)}",
                    "market_id": market_id
                }
            
            # Analyze opportunity with enhanced tracking
            try:
                analysis = await decision_maker.analyze_opportunity(research_data)
                logger.info(f"Analysis completed for market {market_id}")
            except Exception as e:
                logger.error(f"Analysis failed for market {market_id}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Analysis failed: {str(e)}",
                    "market_id": market_id,
                    "research_data": research_data
                }
            
            # Prepare the execution result
            result = {
                "market_id": market_id,
                "success": True
            }
            
            # Execute trade if recommended
            if analysis.get('bet_recommendation'):
                try:
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
                        logger.info(f"Trade executed for market {market_id}")
                    else:
                        result.update({
                            "success": False,
                            "reason": "Failed validation",
                            "details": "Trade recommendation did not pass validation checks"
                        })
                except Exception as e:
                    logger.error(f"Trade execution failed for market {market_id}: {str(e)}")
                    result.update({
                        "success": False,
                        "error": f"Trade execution failed: {str(e)}",
                        "reason": "Execution error"
                    })
            else:
                result.update({
                    "success": False,
                    "reason": "No trading opportunity",
                    "details": "Analysis did not recommend a trade"
                })
            
            # Log execution with enhanced data
            execution_data = {
                "market_id": market_id,
                "research_data": research_data,
                "analysis": analysis,
                "result": result
            }
            
            self.log_execution(execution_data)
            return result
            
        except Exception as e:
            logger.error(f"Error in market crew execution: {str(e)}")
            await self.handle_error(e, {"market_id": market_id})
            return {"success": False, "error": str(e)}

    async def monitor_positions(self) -> List[Dict]:
        """Monitor all active positions with enhanced reporting."""
        try:
            executor = next((a for a in self.agents if a.role == 'Market Executor'), None)
            if not executor:
                raise ValueError("Could not find executor agent")
                
            positions = await executor.monitor_positions()
            
            # Generate position monitoring report
            report = "=== POSITION MONITORING REPORT ===\n"
            for pos in positions:
                report += f"\nMarket: {pos['market_id']}\n"
                report += f"Current P/L: {pos['profit_loss']:.2f}\n"
                report += f"Status: {'Resolved' if pos['is_resolved'] else 'Active'}\n"
                report += "-" * 30
            
            print(report)
            return positions
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}")
            raise

    def get_current_report_path(self) -> str:
        """Get the path to the current consolidated report."""
        return self._report_formatter.get_current_report_path()