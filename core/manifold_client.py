import aiohttp
import asyncio
from typing import Dict, List, Optional
from config.settings import settings
import random

class ManifoldClient:
    def __init__(self):
        self.api_key = settings.MANIFOLD_API_KEY
        self.base_url = "https://api.manifold.markets/v0"
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make an HTTP request to the Manifold API."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/{endpoint}"
            async with session.request(method, url, headers=self.headers, json=data) as response:
                response.raise_for_status()
                return await response.json()
    
    
    async def get_markets(self, limit: int = 50) -> List[Dict]:
        """Get list of markets."""
        # First get a list of market IDs to help with random selection
        all_markets = await self._make_request("GET", "markets?limit=100")
        if not all_markets:
            return []
            
        # Randomly select a starting point
        start_idx = random.randint(0, max(0, len(all_markets) - limit - 1))
        
        # If we have a random starting point, use that market's ID as the 'before' parameter
        if start_idx > 0:
            before_id = all_markets[start_idx]['id']
            return await self._make_request("GET", f"markets?limit={limit}&before={before_id}")
        
        # If we're starting from the beginning, just get the first batch
        return await self._make_request("GET", f"markets?limit={limit}")

    async def get_market(self, market_id: str) -> Dict:
        """Get details of a specific market."""
        return await self._make_request("GET", f"market/{market_id}")
    
    async def place_bet(self, market_id: str, amount: float, outcome: str, probability: float) -> Dict:
        """Place a bet on a market with enhanced debugging."""
        try:
            # Get current market state
            market = await self.get_market(market_id)
            print(f"\nDEBUG: Current market state:")
            print(f"Current probability: {market.get('probability')}")
            print(f"Our target probability: {probability}")
            
            # Format probability to two decimal places
            formatted_prob = round(probability, 2)
            
            data = {
                "contractId": market_id,
                "amount": amount,
                "outcome": outcome,
                "limitProb": formatted_prob
            }
            
            print(f"\nDEBUG: Sending bet data:")
            print(f"Amount: {amount}")
            print(f"Outcome: {outcome}")
            print(f"Limit Probability: {formatted_prob}")
            
            result = await self._make_request(
                "POST", 
                "bet",
                data
            )
            
            print(f"\nDEBUG: Bet response details:")
            print(f"Filled?: {result.get('isFilled')}")
            print(f"Cancelled?: {result.get('isCancelled')}")
            print(f"Actual amount filled: {result.get('amount')}")
            print(f"Shares received: {result.get('shares')}")
            print(f"Prob before: {result.get('probBefore')}")
            print(f"Prob after: {result.get('probAfter')}")
            
            if not result.get('isFilled'):
                print("\nDEBUG: Order not filled. Possible reasons:")
                if result.get('probBefore', 0) > formatted_prob:
                    print("- Limit probability is below market probability")
                if result.get('amount', 0) == 0:
                    print("- Order amount may be too small")
                if result.get('isCancelled'):
                    print("- Order was cancelled")
                    
            return result
            
        except Exception as e:
            print(f"\nDEBUG: Error placing bet: {str(e)}")
            raise



    async def get_my_bets(self) -> List[Dict]:
        """Get list of user's bets."""
        return await self._make_request("GET", "bets")
    
    async def get_market_positions(self, market_id: str) -> Dict:
        """Get current positions in a market."""
        try:
            return await self._make_request("GET", f"market/{market_id}/positions")
        except aiohttp.ClientError as e:
            # Log the error but return an empty dict rather than failing
            print(f"Error fetching positions for market {market_id}: {str(e)}")
            return {"positions": []}
    

    async def search_markets(self, query: str) -> List[Dict]:
        """Search for markets matching query."""
        return await self._make_request("GET", f"markets/search?term={query}")