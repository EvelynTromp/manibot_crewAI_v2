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
        Perform a Google Custom Search with rate limiting.
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
                    
                    if response.status == 429:
                        # Handle rate limit exceeded
                        await asyncio.sleep(self.min_delay * 2)  # Wait longer on rate limit
                        return []  # Return empty results rather than failing
                        
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
                    
        except Exception as e:
            print(f"Search error for query '{query}': {str(e)}")
            return []  # Return empty results rather than failing
    
    async def search_and_summarize(self, query: str, num_results: int = 5) -> str:
        """
        Search and create a summary of findings with rate limiting.
        """
        results = await self.search(query, num_results)
        
        if not results:
            return f"No results found for: {query}"
        
        summary = f"Search Results for: {query}\n\n"
        for i, result in enumerate(results, 1):
            summary += f"{i}. {result['title']}\n"
            summary += f"   URL: {result['link']}\n"
            summary += f"   Summary: {result['snippet']}\n\n"
        
        return summary