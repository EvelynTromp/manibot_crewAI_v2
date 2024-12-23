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
        asyncio.create_task(self._log_user_identity())

        # Rate limiting parameters
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds

            
    async def _log_user_identity(self):
        """Verify and log the authenticated user's identity."""
        try:
            # Call the /me endpoint to get user information
            me_data = await self._make_request("GET", "me")
            logger.info(f"Authenticated as Manifold user: {me_data.get('username')} (ID: {me_data.get('id')})")
            self.user_id = me_data.get('id')
            self.username = me_data.get('username')
        except Exception as e:
            logger.error(f"Failed to verify Manifold identity: {str(e)}")


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



    async def validate_bet_parameters(self, amount: float) -> bool:
        """
        Validates if a bet can be placed by checking user's balance and other constraints.
        This helps prevent failed trades before we attempt them.
        """
        try:
            # Get user balance
            me_data = await self._make_request("GET", "me")
            balance = float(me_data.get('balance', 0))
            
            # Log balance information for debugging
            logger.info(f"Current Manifold balance: M${balance}")
            logger.info(f"Attempting to bet: M${amount}")
            
            if amount > balance:
                logger.error(f"Insufficient balance. Required: M${amount}, Available: M${balance}")
                return False
                
            if amount <= 0:
                logger.error("Invalid bet amount: Must be greater than 0")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating bet parameters: {str(e)}")
            return False

    async def place_bet(self, market_id: str, amount: float, outcome: str, probability: float) -> Dict:
        """Places a bet on a market with comprehensive validation and logging."""
        try:
            # First validate the bet parameters
            if not await self.validate_bet_parameters(amount):
                raise ValueError("Bet validation failed - check balance and parameters")
            
            # Validate inputs
            if outcome not in ["YES", "NO"]:
                raise ValueError("Outcome must be YES or NO")
            if not (0 < probability < 1):
                raise ValueError("Probability must be between 0 and 1")
            
            # Prepare bet data
            data = {
                "contractId": market_id,
                "amount": amount,
                "outcome": outcome,
                "limitProb": round(probability, 3)
            }
            
            # Log the exact request being sent
            logger.info(f"Sending bet request to Manifold API: {json.dumps(data, indent=2)}")
            
            # Place the bet
            try:
                result = await self._make_request("POST", "bet", data=data)
                
                # Log the complete API response
                logger.info(f"Received API response: {json.dumps(result, indent=2)}")
                
                if not result:
                    raise ValueError("Empty response from Manifold API")
                
                # Verify the bet was placed successfully
                if 'id' not in result:
                    raise ValueError("No bet ID in response - bet may have failed")
                    
                return result
                
            except Exception as e:
                logger.error(f"API error during bet placement: {str(e)}")
                if hasattr(e, 'status'):
                    logger.error(f"HTTP Status: {e.status}")
                raise
                
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