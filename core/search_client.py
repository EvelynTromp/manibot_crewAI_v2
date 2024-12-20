import aiohttp
import asyncio
from typing import List, Dict
from config.settings import settings

class SearchClient:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.search_engine_id = "818cb3804f70c47ce"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self._last_request_time = 0
        self.min_delay = 2.0  # Minimum delay between requests in seconds
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform a Google Custom Search with better error handling and logging.
        """
        # Implement rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.min_delay:
            delay = self.min_delay - time_since_last_request
            await asyncio.sleep(delay)
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    
                    # Log the response status and headers for debugging
                    # print(f"Search response status: {response.status}")
                    # print(f"Response headers: {response.headers}")
                    
                    if response.status == 429:
                        print("Rate limit exceeded, waiting before retry")
                        await asyncio.sleep(self.min_delay * 2)
                        raise Exception("Rate limit exceeded")
                        
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Log the raw response data for debugging
                    # print(f"Raw API response: {data}")
                    
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
                        # print(f"No items in response. Full response: {data}")
                        if "error" in data:
                            raise Exception(f"API error: {data['error']}")
                        return []
                        
        except Exception as e:
            print(f"Detailed search error for query '{query}': {str(e)}")
            # Re-raise the exception instead of returning empty results
            raise
    
    async def search_and_summarize(self, query: str, num_results: int = 5) -> str:
        """
        Search and create a summary of findings with better error handling.
        """
        try:
            results = await self.search(query, num_results)
            
            if not results:
                # Check if we have a saved API key
                if not self.api_key:
                    return "Error: No API key configured"
                return f"No results found for query: {query} (API working but no matches)"
            
            summary = f"Search Results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                summary += f"{i}. {result['title']}\n"
                summary += f"   URL: {result['link']}\n"
                summary += f"   Summary: {result['snippet']}\n\n"
            
            return summary
            
        except Exception as e:
            return f"Search error: {str(e)}"