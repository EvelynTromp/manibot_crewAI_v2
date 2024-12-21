import aiohttp
import asyncio
from typing import List, Dict
from config.settings import settings
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class SearchClient:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.search_engine_id = "818cb3804f70c47ce"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self._last_request_time = 0
        self.min_delay = 2.0  # Minimum delay between requests in seconds
    
    def _clean_query(self, query: str) -> str:
        """
        Clean and prepare a query string for the search API.
        Removes quotes and properly encodes the query.
        """
        # Remove any existing quotes
        cleaned = query.replace('"', '').replace("'", '')
        # Remove any special prefixes that might have been added
        cleaned = cleaned.replace('QUERY:', '').strip()
        # URL encode the cleaned query
        return urllib.parse.quote(cleaned)
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform a Google Custom Search with better error handling and logging.
        """
        # Clean and encode the query
        cleaned_query = self._clean_query(query)
        logger.info(f"Original query: {query}")
        logger.info(f"Cleaned query: {cleaned_query}")
        
        # Implement rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.min_delay:
            delay = self.min_delay - time_since_last_request
            await asyncio.sleep(delay)
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": cleaned_query,
            "num": min(num_results, 10)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    
                    logger.debug(f"Search request URL: {response.url}")
                    logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 429:
                        logger.warning("Rate limit exceeded, waiting before retry")
                        await asyncio.sleep(self.min_delay * 2)
                        raise Exception("Rate limit exceeded")
                        
                    response.raise_for_status()
                    data = await response.json()
                    
                    results = []
                    if "items" in data:
                        for item in data["items"]:
                            result = {
                                "title": item.get("title", ""),
                                "link": item.get("link", ""),
                                "snippet": item.get("snippet", "")
                            }
                            results.append(result)
                        return results
                    else:
                        if "error" in data:
                            logger.error(f"API error response: {data['error']}")
                            raise Exception(f"API error: {data['error'].get('message', 'Unknown error')}")
                        logger.warning(f"No search results found for query: {cleaned_query}")
                        return []
                        
        except Exception as e:
            logger.error(f"Search error for query '{cleaned_query}': {str(e)}")
            raise
    
    async def search_and_summarize(self, query: str, num_results: int = 5) -> str:
        """
        Search and create a summary of findings with better error handling.
        """
        try:
            results = await self.search(query, num_results)
            
            if not results:
                if not self.api_key:
                    return "Error: No API key configured"
                return f"No results found for query: {query}"
            
            summary = f"Search Results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                summary += f"{i}. {result['title']}\n"
                summary += f"   URL: {result['link']}\n"
                summary += f"   Summary: {result['snippet']}\n\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in search_and_summarize: {str(e)}")
            return f"Search error: {str(e)}"