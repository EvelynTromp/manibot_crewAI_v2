from crewai import Agent
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from core.search_client import SearchClient
from core.manifold_client import ManifoldClient
from config.settings import settings

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
            # Add more position analysis as needed
        
        return summary

    async def get_active_markets(self, limit: int = 10) -> List[Dict]:
        """Get a list of active markets that meet research criteria."""
        markets = await self.manifold_client.get_markets(limit=limit)
        
        # Filter for interesting markets
        active_markets = []
        for market in markets:
            # Add markets that meet certain criteria
            if self._is_market_interesting(market):
                active_markets.append(market)
        
        return active_markets[:limit]

    def _is_market_interesting(self, market: Dict) -> bool:
        """Determine if a market is interesting for research."""
        # Market should be active
        if market.get('isResolved', False):
            return False
        
        # Market should have sufficient liquidity
        min_liquidity = 100  # Minimum liquidity threshold
        if float(market.get('totalLiquidity', 0)) < min_liquidity:
            return False
        
        # Market should have reasonable time until resolution
        # Add more criteria as needed
        
        return True