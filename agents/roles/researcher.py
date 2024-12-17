from crewai import Agent
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from core.search_client import SearchClient
from core.manifold_client import ManifoldClient
from config.settings import settings
from datetime import datetime, timezone
import logging

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

    async def get_active_markets(self, limit: int = 3) -> List[Dict]:
        """Get a filtered list of promising active markets."""
        # Get more markets initially to ensure we have enough after filtering
        initial_limit = limit * 3
        markets = await self.manifold_client.get_markets(limit=initial_limit)
        
        # Filter for interesting markets
        active_markets = []
        for market in markets:
            if self._is_market_interesting(market):
                # Add this line to enrich market data with metrics
                market['metrics'] = await self._calculate_market_metrics(market)
                active_markets.append(market)
        
        return active_markets[:limit]
  
    def _is_market_interesting(self, market: Dict) -> bool:
        """
        Determine if a market is interesting for research using enhanced filtering criteria.
        Returns True if the market meets our trading criteria.
        """
        # Basic market status checks
        if market.get('isResolved', False) or market.get('isClosed', False):
            return False

        # Get key metrics
        total_liquidity = float(market.get('totalLiquidity', 0))
        volume = float(market.get('volume', 0))
        
        # Let's comment out the traders check for now since the API might be returning this differently
        # traders = market.get('traders', [])
        # unique_traders = len(traders) if traders else 0
        
        # Enhanced filtering criteria - focusing on liquidity and volume for now
        min_liquidity = 10
        min_volume = 3
        
        # Check criteria
        meets_criteria = all([
            total_liquidity >= min_liquidity,
            volume >= min_volume,
            # We'll remove the traders check for now
            # unique_traders >= min_traders
        ])

        return meets_criteria  
    
    
    async def get_active_markets(self, limit: int = 10) -> List[Dict]:
        """Get a filtered list of promising active markets."""
        # Get more markets initially to ensure we have enough after filtering
        initial_limit = limit * 3
        print(f"Fetching initial {initial_limit} markets...")  # Debug print
        
        markets = await self.manifold_client.get_markets(limit=initial_limit)
        print(f"Actually received {len(markets)} markets from API")  # Debug print
        
        # Filter for interesting markets
        active_markets = []
        for market in markets:
            print(f"\nAnalyzing market: {market.get('question', 'No question')}") # Debug print
            print(f"Liquidity: {market.get('totalLiquidity', 0)}")
            print(f"Traders: {len(market.get('traders', []))}")
            print(f"Volume: {market.get('volume', 0)}")
            
            if self._is_market_interesting(market):
                print("Market passed filters!")  # Debug print
                market['metrics'] = await self._calculate_market_metrics(market)
                active_markets.append(market)
            else:
                print("Market filtered out")  # Debug print
        
        # Sort markets by potential
        sorted_markets = sorted(
            active_markets,
            key=lambda x: (
                float(x.get('totalLiquidity', 0)), 
                len(x.get('traders', [])),
                float(x.get('volume', 0))
            ),
            reverse=True
        )
        
        print(f"\nFound {len(sorted_markets)} markets after filtering")  # Debug print
        return sorted_markets[:limit]
    


    def _is_market_interesting(self, market: Dict) -> bool:
        """
        Determine if a market is interesting for research using enhanced filtering criteria.
        Returns True if the market meets our trading criteria.
        """
        print("\nChecking market criteria:")  # Debug print
        
        # Basic market status checks
        if market.get('isResolved', False) or market.get('isClosed', False):
            print("Market rejected: Already resolved or closed")
            return False

        # Get key metrics
        total_liquidity = float(market.get('totalLiquidity', 0))
        volume = float(market.get('volume', 0))
        traders = market.get('traders', [])
        unique_traders = len(traders) if traders else 0
        created_time = market.get('createdTime')
        
        print(f"Metrics found:")  # Debug prints
        print(f"- Total liquidity: {total_liquidity}")
        print(f"- Volume: {volume}")
        print(f"- Unique traders: {unique_traders}")
        
        # Let's make the criteria more lenient
        min_liquidity = 10  # Reduced from 20
        min_traders = 2    # Reduced from 3
        min_volume = 3     # Reduced from 5
        
        # Check each criterion separately and print results
        liquidity_ok = total_liquidity >= min_liquidity
        traders_ok = unique_traders >= min_traders
        volume_ok = volume >= min_volume
        
        print(f"\nCriteria check results:")
        print(f"- Liquidity >= {min_liquidity}: {liquidity_ok}")
        print(f"- Traders >= {min_traders}: {traders_ok}")
        print(f"- Volume >= {min_volume}: {volume_ok}")
        
        meets_criteria = all([
            liquidity_ok,
            traders_ok,
            volume_ok
        ])
        
        if meets_criteria:
            print("Market accepted: Meets all criteria")
        else:
            print("Market rejected: Failed to meet all criteria")
            
        return meets_criteria