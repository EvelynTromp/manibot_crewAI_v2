# core/manifold_client.py

import aiohttp
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone
import random

logger = logging.getLogger(__name__)

class ManifoldClient:
    """
    A client for interacting with the Manifold Markets API.
    
    This client handles all market operations including:
    - Fetching market data
    - Placing bets
    - Managing positions
    - Retrieving user betting history
    
    It includes built-in rate limiting and error handling to ensure reliable operation.
    """
    
    def __init__(self, api_key: str):
        # Initialize core client attributes
        self.api_key = api_key
        self.base_url = "https://api.manifold.markets/v0"
        self.headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting parameters
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds

    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          data: Optional[Dict] = None,
                          params: Optional[Dict] = None) -> Dict:
        """
        Makes a rate-limited request to the Manifold API with comprehensive error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to call
            data: Optional JSON data for POST requests
            params: Optional query parameters
            
        Returns:
            Dict containing the API response
            
        Raises:
            Various exceptions with detailed error messages
        """
        # Implement basic rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                
                # Log request details for debugging
                logger.debug(f"Making {method} request to {url}")
                if data:
                    logger.debug(f"Request data: {data}")
                if params:
                    logger.debug(f"Request params: {params}")
                
                async with session.request(
                    method, 
                    url, 
                    headers=self.headers,
                    json=data,
                    params=params
                ) as response:
                    # Update rate limiting timestamp
                    self.last_request_time = asyncio.get_event_loop().time()
                    
                    # Handle various response status codes
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logger.warning("Rate limit exceeded, implementing backoff")
                        await asyncio.sleep(5)  # Basic backoff
                        raise Exception("Rate limit exceeded")
                    elif response.status == 401:
                        raise Exception("Unauthorized - check API key")
                    elif response.status == 404:
                        raise Exception(f"Resource not found: {endpoint}")
                    else:
                        # For other errors, try to get error details from response
                        try:
                            error_data = await response.json()
                            error_msg = error_data.get('message', 'Unknown error')
                        except:
                            error_msg = await response.text()
                        raise Exception(f"API error ({response.status}): {error_msg}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error in API request: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in API request: {str(e)}")
            raise

    async def get_markets(self, limit: int = 50) -> List[Dict]:
        """
        Fetches a list of markets with random offset to ensure diverse market coverage.
        
        Args:
            limit: Maximum number of markets to return
            
        Returns:
            List of market dictionaries
        """
        try:
            # First get a larger set of markets for random sampling
            all_markets = await self._make_request(
                "GET", 
                "markets",
                params={"limit": 100}  # Get more than we need for better sampling
            )
            
            if not all_markets:
                logger.warning("No markets returned from API")
                return []
            
            # Randomly select a starting point
            if len(all_markets) > limit:
                start_idx = random.randint(0, len(all_markets) - limit)
                return all_markets[start_idx:start_idx + limit]
            
            return all_markets[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching markets: {str(e)}")
            raise

    async def get_market(self, market_id: str) -> Dict:
        """
        Fetches detailed information about a specific market.
        
        Args:
            market_id: Unique identifier for the market
            
        Returns:
            Dictionary containing market details
        """
        return await self._make_request("GET", f"market/{market_id}")

    async def place_bet(self, 
                       market_id: str, 
                       amount: float, 
                       outcome: str, 
                       probability: float) -> Dict:
        """
        Places a bet on a market with comprehensive validation and debugging.
        
        Args:
            market_id: Market to bet on
            amount: Bet amount in M$
            outcome: YES or NO
            probability: Target probability as decimal
            
        Returns:
            Dictionary containing bet details and confirmation
        """
        try:
            # Validate inputs
            if outcome not in ["YES", "NO"]:
                raise ValueError("Outcome must be YES or NO")
            if not (0 < probability < 1):
                raise ValueError("Probability must be between 0 and 1")
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            # Get current market state for validation
            market = await self.get_market(market_id)
            logger.info(f"Current market probability: {market.get('probability')}")
            logger.info(f"Target probability: {probability}")
            
            # Prepare bet data
            data = {
                "contractId": market_id,
                "amount": amount,
                "outcome": outcome,
                "limitProb": round(probability, 3)  # Round to 3 decimal places
            }
            
            # Place the bet
            result = await self._make_request("POST", "bet", data=data)
            
            # Log bet execution details
            logger.info(f"Bet placed: {amount}M$ on {outcome} at {probability}")
            logger.info(f"Filled: {result.get('isFilled')}")
            logger.info(f"Shares received: {result.get('shares')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing bet: {str(e)}")
            raise

    async def get_my_positions(self) -> List[Dict]:
        """
        Fetches all current user positions.
        
        Returns:
            List of position dictionaries
        """
        return await self._make_request("GET", "bets")

    async def get_market_positions(self, market_id: str) -> Dict:
        """
        Fetches all positions for a specific market.
        
        Args:
            market_id: Market to get positions for
            
        Returns:
            Dictionary containing position information
        """
        try:
            return await self._make_request("GET", f"market/{market_id}/positions")
        except Exception as e:
            # Return empty positions rather than failing
            logger.warning(f"Error fetching positions for market {market_id}: {str(e)}")
            return {"positions": []}

    async def search_markets(self, query: str) -> List[Dict]:
        """
        Searches for markets matching a query string.
        
        Args:
            query: Search term
            
        Returns:
            List of matching market dictionaries
        """
        # URL encode the query
        safe_query = query.replace(' ', '+')
        return await self._make_request("GET", f"markets/search?term={safe_query}")