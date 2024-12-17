import aiohttp
import asyncio
from typing import Dict, List, Optional
from config.settings import settings

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
        return await self._make_request("GET", f"markets?limit={limit}")
    
    async def get_market(self, market_id: str) -> Dict:
        """Get details of a specific market."""
        return await self._make_request("GET", f"market/{market_id}")
    
        # In manifold_client.py, modify the place_bet method:
    async def place_bet(self, market_id: str, amount: float, outcome: str, probability: float) -> Dict:
        """Place a bet on a market.
        
        Args:
            market_id (str): The ID of the market to bet on
            amount (float): Amount to bet in M$
            outcome (str): For binary markets: 'YES' or 'NO'
            probability (float): Your probability estimate
        """
        try:
            # Format probability to two decimal places
            formatted_prob = round(probability, 2)
            
            data = {
                "contractId": market_id,
                "amount": amount,
                "outcome": outcome,
                "limitProb": formatted_prob  # Changed from probability to limitProb
            }
            
            print(f"Placing bet with data: {data}")
            
            result = await self._make_request(
                "POST", 
                "bet",
                data
            )
            print(f"Bet result: {result}")
            return result
            
        except Exception as e:
            print(f"Error placing bet: {str(e)}")
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