# core/manifold_client.py

import aiohttp
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone
import random
import json

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
        # Implement exponential backoff for rate limiting
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/{endpoint}"
                    
                    # Log request details for debugging
                    logger.debug(f"Making {method} request to {url}")
                    if data:
                        logger.debug(f"Request data: {json.dumps(data, indent=2)}")
                    if params:
                        logger.debug(f"Request params: {params}")
                    
                    async with session.request(
                        method, 
                        url, 
                        headers=self.headers,
                        json=data,
                        params=params,
                        timeout=30  # Add timeout to prevent hanging
                    ) as response:
                        
                        # Handle various response status codes
                        if response.status == 429:  # Rate limit exceeded
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Rate limit exceeded, waiting {delay}s before retry")
                            await asyncio.sleep(delay)
                            continue
                            
                        response_text = await response.text()
                        
                        try:
                            response_data = json.loads(response_text)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON response: {response_text}")
                            raise ValueError("Invalid API response format")
                        
                        if response.status == 200:
                            return response_data
                        elif response.status == 401:
                            raise ValueError("Unauthorized - check API key")
                        elif response.status == 404:
                            raise ValueError(f"Resource not found: {endpoint}")
                        else:
                            error_msg = response_data.get('message', 'Unknown error')
                            logger.error(f"API error ({response.status}): {error_msg}")
                            raise ValueError(f"API error: {error_msg}")
                            
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Network error in API request: {str(e)}")
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(base_delay * (2 ** attempt))
                
            except Exception as e:
                logger.error(f"Error in API request: {str(e)}", exc_info=True)
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

    
    async def validate_bet_parameters(self, market_id: str, amount: float, probability: float) -> bool:
        """
        Comprehensive validation of bet parameters including balance check, market status,
        and sanity checks for the bet amount and probability.
        
        Returns:
            bool: True if all validations pass, False otherwise
        """
        try:
            # Get user balance and account info
            me_data = await self._make_request("GET", "me")
            balance = float(me_data.get('balance', 0))
            username = me_data.get('username', 'Unknown')
            user_id = me_data.get('id', 'Unknown')
            
            # Get market data
            market = await self._make_request("GET", f"market/{market_id}")
            
            # Log current state for debugging
            logger.info(f"Account: {username} (ID: {user_id})")
            logger.info(f"Current Manifold balance: M${balance}")
            logger.info(f"Attempting to bet: M${amount}")
            
            # Validate market is still active
            if market.get('isResolved'):
                logger.error(f"Market {market_id} is already resolved")
                return False
                
            close_time = market.get('closeTime')
            if close_time and close_time < time.time() * 1000:
                logger.error(f"Market {market_id} is closed")
                return False
                
            # Validate market type
            if market.get('outcomeType') != 'BINARY':
                logger.error(f"Market {market_id} is not a binary type")
                return False
                
            # Validate bet amount
            if amount > balance:
                logger.error(f"Insufficient balance for account {username}. Required: M${amount}, Available: M${balance}")
                return False
                
            if amount <= 0:
                logger.error(f"Invalid bet amount for account {username}: Must be greater than 0")
                return False
                
            # Validate probability
            market_prob = float(market.get('probability', 0.5))
            if abs(probability - market_prob) > 0.5:
                logger.warning(f"Large probability difference. Market: {market_prob}, Bet: {probability}")
                
            # All validations passed
            logger.info(f"Bet parameters validated successfully for market {market_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating bet parameters: {str(e)}", exc_info=True)
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
            
            market = await self._make_request("GET", f"market/{market_id}")
            
                    # Validate market type
            if market.get('outcomeType') != 'BINARY':
                raise ValueError("Market is not a binary type")
            
            # Get market data to check type
            
            # Prepare bet data based on market type
            data = {
                "amount": amount,
                "contractId": market_id
            }
            
            # Handle binary markets
            if market.get('outcomeType') == 'BINARY':
                data["outcome"] = outcome
                data["limitProb"] = round(probability, 3)
            else:
                # We shouldn't get here due to market filtering, but just in case
                raise ValueError("Market is not a binary type")
            
            # Log the exact request being sent
            logger.info(f"Sending bet request to Manifold API: {json.dumps(data, indent=2)}")
            
            # Place the bet
            try:
                # Prepare bet data
                data = {
                    "amount": amount,
                    "contractId": market_id,
                    "outcome": outcome,
                    "limitProb": round(probability, 3)
                }
                
                # Log the exact request being sent
                logger.debug(f"Sending bet request: {json.dumps(data, indent=2)}")
                
                result = await self._make_request("POST", "bet", data=data)
                
                # Log the complete API response
                logger.debug(f"Received API response: {json.dumps(result, indent=2)}")
                
                if not result:
                    raise ValueError(f"Empty response from Manifold API")
                    
                if 'id' not in result:
                    # Log additional details about the failed response
                    logger.error(f"Invalid API response structure: {json.dumps(result, indent=2)}")
                    raise ValueError(f"No bet ID in response - full response: {result}")
        
                logger.info(f"Successfully placed bet {result['id']} on market {market_id}")
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