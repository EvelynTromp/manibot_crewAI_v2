# crews/market_crew.py

from typing import Dict, List, Optional
from core.gpt_client import GPTClient
from utils.logger import get_logger
from config.settings import settings
from crews.base_crew import BaseCrew
from agents.roles.decision_maker import DecisionMakerAgent
from agents.roles.executor import ExecutorAgent
from crewai import Agent  # Add this line
from pydantic import Field
from crewai import Crew
from typing import Optional
import backoff 
import asyncio
from datetime import datetime



logger = get_logger(__name__)


class MarketCrew(BaseCrew):
    """Enhanced crew for market analysis with improved execution handling."""
    
    gpt_client: Optional[GPTClient] = Field(default=None)
    
    def __init__(self):
        decision_maker = DecisionMakerAgent()
        executor = ExecutorAgent()
        
        super().__init__(
            agents=[decision_maker, executor],
            tasks=[],
            verbose=True
        )
        
        self.gpt_client = GPTClient()
        logger.info("Market crew initialized with enhanced execution capabilities")
    
    def backoff_handler(details):
        """Handler for backoff events."""
        logger.warning(f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries")

    @backoff.on_exception(
        backoff.expo,
        (asyncio.TimeoutError, Exception),
        max_tries=3,
        on_backoff=backoff_handler
    )
    async def scan_markets(self, limit: int = 1) -> List[Dict]:
        """Scan markets with improved async handling and backoff."""
        try:
            self.start_scan_session()
            logger.info(f"Starting market scan for {limit} markets")
            
            executor = self._get_agent_by_role('Market Executor')
            if not executor:
                raise ValueError("Could not find executor agent")
            
            # Get markets with timeout
            active_markets = await asyncio.wait_for(
                executor.manifold_client.get_markets(limit),
                timeout=settings.SEARCH_TIMEOUT
            )
            
            logger.info(f"Found {len(active_markets)} active markets to analyze")
            
            results = []
            executed_trades = 0
            
            for i, market in enumerate(active_markets, 1):
                try:
                    result = await self.analyze_and_trade(market['id'])
                    results.append(result)
                    
                    if result.get('trade_executed'):
                        executed_trades += 1
                        logger.info(f"Successfully executed trade for market {market['id']}")
                    
                    # Add progressive delay between markets
                    if i < len(active_markets):
                        delay = settings.RATE_LIMIT_DELAY * (1 + (i * 0.1))
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"Error processing market {market['id']}: {str(e)}")
                    results.append({
                        "market_id": market['id'],
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(f"Scan complete. Executed {executed_trades} trades out of {len(active_markets)} markets")
            return results
            
        except Exception as e:
            logger.error(f"Error in market scan: {str(e)}")
            return []    

    async def analyze_and_trade(self, market_id: str) -> Dict:
        """Analyze market and execute trade with comprehensive error handling and logging."""
        execution_data = {
            "market_id": market_id,
            "success": False,
            "trade_executed": False,
            "error": None,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Get required agents with validation
            executor = self._get_agent_by_role('Market Executor')
            if not executor:
                raise ValueError("Required executor agent not found")
            
            # Fetch market data with timeout and retry
            try:
                market_data = await asyncio.wait_for(
                    executor.manifold_client.get_market(market_id),
                    timeout=settings.SEARCH_TIMEOUT
                )
                execution_data["market_data"] = market_data
                logger.info(f"Retrieved market data for {market_id}")
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout fetching market data for {market_id}")
            except Exception as e:
                raise RuntimeError(f"Error fetching market data: {str(e)}")
            
            # Perform market analysis with detailed error tracking
            try:
                analysis = await self.gpt_client.analyze_market(market_data)
                execution_data["analysis"] = analysis
                
                if analysis.get('error'):
                    logger.warning(f"Analysis completed with error: {analysis['error']}")
                    execution_data["error"] = analysis['error']
                elif not analysis.get('success', False):
                    logger.warning("Analysis completed but marked as unsuccessful")
                    execution_data["error"] = "Analysis failed to produce valid results"
                else:
                    logger.info(f"Successfully analyzed market {market_id}")
                    execution_data["success"] = True
            except Exception as e:
                raise RuntimeError(f"Error in market analysis: {str(e)}")
            
            # Attempt trade execution if analysis was successful and recommended
            if execution_data["success"] and analysis.get('bet_recommendation'):
                try:
                    trade_result = await executor.execute_trade(
                        market_id,
                        analysis,
                        {'market_data': market_data}
                    )
                    
                    execution_data.update(trade_result)
                    if trade_result.get('success'):
                        execution_data['trade_executed'] = True
                        logger.info(f"Successfully executed trade for market {market_id}")
                    else:
                        logger.warning(f"Trade execution failed: {trade_result.get('error')}")
                except Exception as e:
                    logger.error(f"Error executing trade: {str(e)}")
                    execution_data["trade_error"] = str(e)
            
            return execution_data
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in analyze_and_trade: {error_msg}")
            execution_data["error"] = error_msg
            return execution_data
        finally:
            # Always log execution data
            execution_data["end_time"] = datetime.now().isoformat()
            self.log_execution(execution_data)
    
    

    def _get_agent_by_role(self, role: str) -> Optional[Agent]:
        """Helper method to get agent by role."""
        return next((agent for agent in self.agents if agent.role == role), None)

    async def monitor_positions(self) -> List[Dict]:
        """Monitor active positions using executor agent."""
        try:
            executor = self._get_agent_by_role('Market Executor')
            if not executor:
                raise ValueError("Could not find executor agent")
                
            return await executor.monitor_positions()
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}")
            raise