# Standard library imports
from datetime import datetime, timezone
import logging

# Type hinting imports
from typing import Dict, List, Optional, Union

# Third-party imports
from crewai import Agent
from pydantic import BaseModel, Field

# Local imports
from core.search_client import SearchClient
from core.manifold_client import ManifoldClient
from config.settings import settings

# Initialize logger
logger = logging.getLogger(__name__)

class ResearcherAgent(Agent):
    """Agent responsible for market research and analysis."""
    
    def __init__(self):
        # Initialize base Agent first
        super().__init__(
            role='Market Researcher',
            goal='Gather and analyze comprehensive market information and relevant research',
            backstory="""You are an expert market researcher with a keen eye for detail 
            and a strong analytical mindset. Your expertise lies in gathering relevant 
            information about prediction markets and synthesizing it into actionable insights.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Initialize instance variables without direct assignment
        self._search_client = None
        self._manifold_client = None
        
    @property
    def search_client(self):
        """Lazy initialization of search client."""
        if self._search_client is None:
            self._search_client = SearchClient()
        return self._search_client
        
    @property
    def manifold_client(self):
        """Lazy initialization of manifold client."""
        if self._manifold_client is None:
            self._manifold_client = ManifoldClient()
        return self._manifold_client

    async def research_market(self, market_id: str) -> Dict:
        """
        Conduct comprehensive research on a specific market.
        
        Args:
            market_id: ID of the Manifold market to research
            
        Returns:
            Dictionary containing market data and research findings
        """
        try:
            # Get market details
            market_data = await self.manifold_client.get_market(market_id)
            
            # Generate search queries based on market question
            question = market_data.get('question', '')
            search_queries = self._generate_search_queries(question)
            
            # Gather research data
            research_findings = []
            for query in search_queries:
                results = await self.search_client.search_and_summarize(query)
                research_findings.append({
                    'query': query,
                    'results': results
                })
            
            # Get market analytics
            positions = await self.manifold_client.get_market_positions(market_id)
            
            return {
                'market_data': market_data,
                'research_findings': research_findings,
                'market_positions': positions,
                'summary': await self._generate_research_summary(market_data, research_findings, positions)
            }
        except Exception as e:
            logger.error(f"Error researching market {market_id}: {str(e)}")
            raise

    def _generate_search_queries(self, question: str) -> List[str]:
        """Generate relevant search queries based on market question."""
        # Base query is the question itself
        queries = [question]
        
        # Add variations
        queries.append(f"latest news {question}")
        queries.append(f"analysis {question}")
        queries.append(f"prediction {question}")
        queries.append(f"expert opinion {question}")
        
        return queries[:settings.MAX_SEARCH_RESULTS]  # Limit number of queries

    async def _generate_research_summary(self, 
                                     market_data: Dict, 
                                     research_findings: List[Dict], 
                                     positions: Dict) -> str:
        """Generate a concise summary of all research findings."""
        summary = f"Research Summary for Market: {market_data.get('question', '')}\n\n"
        
        # Market Overview
        summary += "Market Overview:\n"
        summary += f"- Current probability: {market_data.get('probability', 'N/A')}\n"
        summary += f"- Total trades: {market_data.get('volume', 'N/A')}\n"
        summary += f"- Trading volume: {market_data.get('totalLiquidity', 'N/A')}\n\n"
        
        # Key Research Findings
        summary += "Key Research Findings:\n"
        for finding in research_findings:
            summary += f"\nQuery: {finding['query']}\n"
            summary += f"Findings: {finding['results'][:500]}...\n"  # Truncate for brevity
        
        # Market Position Analysis
        summary += "\nMarket Position Analysis:\n"
        if positions:
            total_positions = len(positions)
            summary += f"- Total unique positions: {total_positions}\n"
        
        return summary

    async def get_active_markets(self, limit: int = 10) -> List[Dict]:
        """Get a filtered list of promising active markets."""
        try:
            # Get more markets initially to ensure we have enough after filtering
            initial_limit = limit * 3
            logger.info(f"Fetching initial {initial_limit} markets...")
            
            markets = await self.manifold_client.get_markets(limit=initial_limit)
            logger.info(f"Received {len(markets)} markets from API")
            
            # Filter for interesting markets
            active_markets = []
            for market in markets:
                logger.info(f"Analyzing market: {market.get('question', 'No question')}")
                logger.info(f"Liquidity: {market.get('totalLiquidity', 0)}")
                logger.info(f"Volume: {market.get('volume', 0)}")
                
                if self._is_market_interesting(market):
                    logger.info("Market passed filters!")
                    market['metrics'] = self._calculate_market_metrics(market)
                    active_markets.append(market)
                else:
                    logger.info("Market filtered out")
            
            # Sort markets by potential
            sorted_markets = sorted(
                active_markets,
                key=lambda x: (
                    float(x.get('totalLiquidity', 0)), 
                    float(x.get('volume', 0))
                ),
                reverse=True
            )
            
            logger.info(f"Found {len(sorted_markets)} markets after filtering")
            return sorted_markets[:limit]
            
        except Exception as e:
            logger.error(f"Error getting active markets: {str(e)}")
            raise

    def _is_market_interesting(self, market: Dict) -> bool:
        """
        Determine if a market is interesting for research using enhanced filtering criteria.
        Returns True if the market meets our trading criteria.
        """
        # Basic market status checks
        if market.get('isResolved', False) or market.get('isClosed', False):
            logger.info("Market rejected: Already resolved or closed")
            return False

        # Get key metrics
        total_liquidity = float(market.get('totalLiquidity', 0))
        volume = float(market.get('volume', 0))
        
        # Criteria thresholds
        min_liquidity = 10  # Reduced from 20
        min_volume = 3     # Reduced from 5
        
        # Check criteria
        liquidity_ok = total_liquidity >= min_liquidity
        volume_ok = volume >= min_volume
        
        meets_criteria = all([liquidity_ok, volume_ok])
        
        if meets_criteria:
            logger.info("Market accepted: Meets all criteria")
        else:
            logger.info("Market rejected: Failed to meet all criteria")
            
        return meets_criteria

    def _calculate_market_metrics(self, market: Dict) -> Dict:
        """
        Calculate additional metrics for market analysis.
        
        Args:
            market: Dictionary containing raw market data
            
        Returns:
            Dictionary containing calculated metrics
        """
        total_liquidity = float(market.get('totalLiquidity', 0))
        volume = float(market.get('volume', 0))
        num_traders = len(market.get('traders', []))
        
        metrics = {
            'liquidity_per_trader': total_liquidity / max(num_traders, 1),
            'volume_per_trader': volume / max(num_traders, 1),
            'trades_per_trader': volume / max(num_traders, 1),
            'market_age_hours': self._calculate_market_age(market.get('createdTime')),
            'activity_score': self._calculate_activity_score(volume, total_liquidity, num_traders)
        }
        
        return metrics

    def _calculate_market_age(self, created_time: Union[str, int]) -> float:
        """
        Calculate market age in hours from either a timestamp string or Unix timestamp.
        
        Args:
            created_time: Either ISO format string or Unix timestamp in milliseconds
            
        Returns:
            Market age in hours as a float
        """
        if not created_time:
            return 0
            
        try:
            if isinstance(created_time, int):
                # Handle Unix timestamp (convert from milliseconds to seconds)
                created_dt = datetime.fromtimestamp(created_time / 1000, tz=timezone.utc)
            else:
                # Handle ISO format string
                created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                
            now = datetime.now(timezone.utc)
            age_hours = (now - created_dt).total_seconds() / 3600
            return age_hours
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Error calculating market age: {str(e)}")
            return 0

    def _calculate_activity_score(self, volume: float, liquidity: float, num_traders: int) -> float:
        """Calculate a normalized activity score (0-1) based on market metrics."""
        # Base score from volume and liquidity
        volume_score = min(volume / 100, 1.0)  # Normalize volume with max of 100
        liquidity_score = min(liquidity / 1000, 1.0)  # Normalize liquidity with max of 1000
        trader_score = min(num_traders / 10, 1.0)  # Normalize traders with max of 10
        
        # Weighted average of scores
        return (volume_score * 0.4 + liquidity_score * 0.4 + trader_score * 0.2)