"""
Web Search Client - Searches the web for verification evidence
Uses DuckDuckGo - 100% FREE, no API key needed!
"""
import time
from typing import List, Dict, Any
from datetime import datetime


class WebSearchClient:
    """
    Web search client using DuckDuckGo.
    Completely FREE - no API key required!
    """
    
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self._ddg = None
        self._initialized = False
    
    def _get_ddg_client(self):
        """Initialize DuckDuckGo client"""
        if self._ddg is None:
            try:
                from duckduckgo_search import DDGS
                self._ddg = DDGS()
                if not self._initialized:
                    print("✓ Web search ready (DuckDuckGo - Free)")
                    self._initialized = True
            except ImportError:
                raise ImportError(
                    "duckduckgo-search package not installed.\n"
                    "Run: pip install duckduckgo-search"
                )
        return self._ddg
    
    def search(self, query: str, retry_count: int = 2) -> List[Dict[str, Any]]:
        """
        Search the web for a query with rate limiting.
        
        Args:
            query: Search query string
            retry_count: Number of retries on rate limit
            
        Returns:
            List of search results with url, title, snippet, source
        """
        for attempt in range(retry_count + 1):
            try:
                # Rate limiting: wait between requests
                time.sleep(1.5)  # Wait 1.5 seconds between searches
                
                ddg = self._get_ddg_client()
                results = list(ddg.text(query, max_results=self.max_results))
                
                processed_results = []
                for result in results:
                    processed_results.append({
                        'url': result.get('href', ''),
                        'title': result.get('title', ''),
                        'snippet': result.get('body', ''),
                        'source': self._extract_source(result.get('href', '')),
                        'timestamp': datetime.now().isoformat()
                    })
                
                return processed_results
                
            except Exception as e:
                if 'Ratelimit' in str(e) and attempt < retry_count:
                    wait_time = (attempt + 1) * 3  # Exponential backoff
                    print(f"   ⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    self._ddg = None  # Reset client
                else:
                    if attempt == retry_count:
                        print(f"   ⚠ Search failed after {retry_count} retries")
                    return []
        
        return []
    
    def _extract_source(self, url: str) -> str:
        """Extract source name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return url
    
    def search_news(self, query: str, days: int = 30) -> List[Dict[str, Any]]:
        """Search recent news articles"""
        try:
            ddg = self._get_ddg_client()
            results = list(ddg.news(query, max_results=self.max_results))
            
            processed_results = []
            for result in results:
                processed_results.append({
                    'url': result.get('url', ''),
                    'title': result.get('title', ''),
                    'snippet': result.get('body', ''),
                    'source': result.get('source', ''),
                    'date': result.get('date', ''),
                    'timestamp': datetime.now().isoformat()
                })
            
            return processed_results
            
        except Exception as e:
            print(f"⚠ News search error: {e}")
            return []
