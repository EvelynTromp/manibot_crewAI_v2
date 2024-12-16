import aiohttp
from typing import List, Dict
from config.settings import settings

class SearchClient:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.search_engine_id = "818cb3804f70c47ce"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform a Google Custom Search and return results.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10)
            
        Returns:
            List of search results with title, link, and snippet
        """
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
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
    
    async def search_and_summarize(self, query: str, num_results: int = 5) -> str:
        """
        Search and create a summary of findings.
        
        Args:
            query: Search query string
            num_results: Number of results to summarize
            
        Returns:
            Formatted string with search results summary
        """
        results = await self.search(query, num_results)
        
        summary = f"Search Results for: {query}\n\n"
        for i, result in enumerate(results, 1):
            summary += f"{i}. {result['title']}\n"
            summary += f"   URL: {result['link']}\n"
            summary += f"   Summary: {result['snippet']}\n\n"
        
        return summary