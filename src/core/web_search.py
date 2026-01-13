"""
Web search utility - Search the web and collect results for LLM synthesis
"""
from typing import List, Dict, Optional
import requests
from dataclasses import dataclass
import time
import json

@dataclass
class SearchResult:
    """Represents a single search result"""
    title: str
    url: str
    snippet: str
    source: str = "web"


class WebSearcher:
    """Web search utility using DuckDuckGo Instant Answer API (free, no key required)"""
    
    def __init__(self, timeout: int = 60):
        """
        Initialize web searcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.base_url = "https://api.duckduckgo.com"
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            num_results: Number of results to return (DuckDuckGo API may return fewer)
            
        Returns:
            List of SearchResult objects
        """
        try:
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/122.0.0.0 Safari/537.36"
            }

            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }

            response = requests.get(self.base_url, params=params, headers=headers, timeout=self.timeout)
            if response.status_code == 202:
                print("Warning: DuckDuckGo API returned 202 Accepted. Results may be incomplete.")
                op_url = response.headers.get("operation-location") or response.headers.get("Operation-Location") or response.headers.get("Location")
                retry_after = int(response.headers.get("Retry-After", 1))
                total_wait = 0
                if not op_url:
                    time.sleep(retry_after)
                    follow_url = self.base_url
                else:
                    follow_url = op_url
                # Poll until ready or timeout
                deadline_time = time.time() + self.timeout
                while time.time() < deadline_time:
                    poll_resp = requests.get(follow_url,  timeout=self.timeout)
                    if poll_resp.status_code in (200, 201):
                        ct = poll_resp.headers.get("Content-Type", "")
                        if "application/json" in ct.lower():
                            data = poll_resp.json()
                        else:
                            data = self._parse_response_safely(poll_resp)[0]
                        break
                    elif poll_resp.status_code == 202:
                        retry_after = int(poll_resp.headers.get("Retry-After", retry_after))
                        wait_seconds = retry_after
                        time.sleep(wait_seconds)
                        continue
                                        
                    else:
                        print(f"Duckduck poll failed: {poll_resp.status_code} {poll_resp.text}")
                        poll_resp.raise_for_status()
                    # update retry_after if provided
                    retry_after = int(poll_resp.headers.get("Retry-After", retry_after))
                else:

                    print("Warning: DuckDuckGo API polling timed out.")
                    return []
            response.raise_for_status()
            
            ct = response.headers.get("Content-Type", "")
            if "application/json" in ct.lower():
                data = response.json()
            else:
                data = self._parse_response_safely(response)[0]
            results = []
            
            # Extract instant answer if available
            if data.get("AbstractText"):
                results.append(SearchResult(
                    title="DuckDuckGo Instant Answer",
                    url=data.get("AbstractURL", ""),
                    snippet=data.get("AbstractText", ""),
                    source="duckduckgo_instant"
                ))
            
            # Extract related topics (limited but relevant)
            if data.get("RelatedTopics"):
                for item in data["RelatedTopics"][:num_results]:
                    if isinstance(item, dict):
                        if "FirstURL" in item:
                            results.append(SearchResult(
                                title=item.get("Text", "").split("|")[0].strip() if "|" in item.get("Text", "") else item.get("Text", ""),
                                url=item.get("FirstURL", ""),
                                snippet=item.get("Text", "").split("|")[-1].strip() if "|" in item.get("Text", "") else item.get("Text", ""),
                                source="duckduckgo_related"
                            ))
            
            # If results are sparse, try a fallback with requests to get more info
            if len(results) < num_results:
                results.extend(self._search_fallback(query, num_results - len(results)))
            
            return results[:num_results]
        
        except Exception as e:
            print(f"Web search failed: {e}")
            return []
    
    def _search_fallback(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Fallback search using a simple web scraping approach (very basic).
        Note: This is a fallback; consider using a proper search API for production.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects (may be empty if fallback fails)
        """
        try:
            # Try Bing search API as alternative (also free tier available)
            # For now, return empty list as a safe fallback
            return []
        except Exception as e:
            print(f"Fallback search failed: {e}")
            return []
    
    def _parse_response_safely(self, resp):
        """
        假设 resp 是 requests.Response 且 status_code==200
        返回: (data, meta)
        - data: 解析出的 Python 对象；若非 JSON，则返回 {'raw_text': ...}
        - meta: 诊断信息字典，便于日志上报和问题定位
        """
        meta = {
            "status_code": resp.status_code,
            "content_type": resp.headers.get("Content-Type", ""),
            "encoding": resp.encoding,
            "content_length": resp.headers.get("Content-Length", ""),
            "url": resp.url,
        }

        # 1) 先尝试直接 json()
        try:
            return resp.json(), meta
        except Exception as e:
            meta["json_error"] = f"{type(e).__name__}: {e}"

        # 2) 如果失败，取文本看看
        text = resp.text or ""
        if not text.strip():
            # 空体：返回空 + 元信息
            meta["empty_body"] = True
            return {"raw_text": ""}, meta

        # 3) 处理 BOM
        raw = resp.content or b""
        if raw.startswith(b"\xef\xbb\xbf"):
            try:
                text = raw.decode("utf-8-sig")
            except Exception as e:
                meta["decode_error_utf8_sig"] = f"{type(e).__name__}: {e}"
                text = raw.decode(resp.encoding or "utf-8", errors="replace")

        # 4) 如果看起来像 JSON，就尝试手动加载
        stripped = text.strip()
        looks_like_json = stripped.startswith("{") or stripped.startswith("[")
        if looks_like_json:
            try:
                # strict=False 可在某些非标准 JSON（比如控制字符）时更宽容
                data = json.loads(stripped)
                return data, meta
            except Exception as e:
                meta["json_loads_error"] = f"{type(e).__name__}: {e}"

        # 5) 到这里仍失败——返回原始文本，并提示可能是 HTML/纯文本
        meta["fallback"] = "return raw_text"
        return {"raw_text": text}, meta



class GoogleSearcher:
    """
    Google Custom Search - More comprehensive but requires API key.
    Optional: Set environment variables GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID to enable.
    """
    
    def __init__(self, api_key: Optional[str] = None, engine_id: Optional[str] = None, timeout: int = 60):
        """
        Initialize Google searcher.
        
        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            engine_id: Google Custom Search Engine ID (or set GOOGLE_SEARCH_ENGINE_ID env var)
            timeout: Request timeout in seconds
        """
        import os
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.engine_id = engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.timeout = timeout
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search using Google Custom Search API.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.api_key or not self.engine_id:
            print("Warning: Google API key or engine ID not configured. Skipping Google search.")
            return []
        
        try:
            params = {
                "q": query,
                "key": self.api_key,
                "cx": self.engine_id,
                "num": min(num_results, 10),  # Google API max is 10
            }
            
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", [])[:num_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="google"
                ))
            
            return results
        
        except Exception as e:
            print(f"Google search failed: {e}")
            return []


class BingSearcher:
    """
    Bing Web Search using Azure/Microsoft Bing Search API.
    Supports either the global endpoint (api.bing.microsoft.com) with
    subscription key or a custom Azure Cognitive Services endpoint.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, timeout: int = 60):
        import os
        # API key can be provided or read from BING_SEARCH_API_KEY env var
        self.api_key = api_key or os.getenv("BING_SEARCH_API_KEY")
        # Endpoint can be provided or read from BING_SEARCH_ENDPOINT env var.
        # If not provided, use the global Microsoft Bing Search endpoint.
        self.endpoint = endpoint or os.getenv("BING_SEARCH_ENDPOINT") or "https://api.bing.microsoft.com/v7.0/search"
        self.timeout = timeout

    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search using Bing Web Search API.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            print("Warning: Bing Search API key not configured (BING_SEARCH_API_KEY). Skipping Bing search.")
            return []

        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": query, "count": min(num_results, 50)}
            response = requests.get(self.endpoint, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            results = []
            web_pages = data.get("webPages", {}).get("value", [])
            for item in web_pages[:num_results]:
                results.append(SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source="bing",
                ))

            return results

        except Exception as e:
            print(f"Bing search failed: {e}")
            try:
                # helpful debug info
                print("Bing response:", response.text)
            except Exception:
                pass
            return []

class SpeedbirdSearcher:
    """
    Bing Web Search using Azure/Microsoft Bing Search API.
    Supports either the global endpoint (api.bing.microsoft.com) with
    subscription key or a custom Azure Cognitive Services endpoint.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, timeout: int = 60):
        import os
        # API key can be provided or read from Speedbird_SEARCH_API_KEY env var
        self.api_key = api_key or os.getenv("Speedbird_SEARCH_API_KEY")
        # Endpoint can be provided or read from Speedbird_SEARCH_ENDPOINT env var.
        # If not provided, use the global Microsoft Bing Search endpoint.
        self.endpoint = endpoint or os.getenv("Speedbird_SEARCH_ENDPOINT") or "https://www.bingapis.com/v3/grounding/search/web"
        self.timeout = timeout

    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search using SpeedBird Web Search API.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            print("Warning: SpeedBird Search API key not configured (SPEEDBIRD_SEARCH_API_KEY). Skipping SpeedBird search.")
            return []
            
        headers = {
            "host": "www.bingapis.com",
            "x-apikey": self.api_key,
            "content-type": "application/json"
        }
        
        payload = {
            "query": query,
            "maxResults": num_results,
            "language": "en",
            "region": "US",
            "maxLength": 3000
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            results = []
            web_pages = data.get("webResults", [])
            for item in web_pages[:num_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source="bing",
                ))
            return results
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

            try:
                # helpful debug info
                print("Bing response:", response.text)
            except Exception:
                pass
            return []
        
def get_searcher(prefer_engine) -> WebSearcher:
    """
    Get a web searcher instance.

    Args:
        prefer_google: If True, return GoogleSearcher if credentials available
        prefer_bing: If True, return BingSearcher if credentials available

    Returns:
        WebSearcher or specific searcher instance
    """
    import os

    # Prefer Bing if requested and API key is provided
    if prefer_engine == "bing" and (os.getenv("BING_SEARCH_API_KEY") or os.getenv("BING_SEARCH_ENDPOINT")):
        return BingSearcher()

    # Prefer Google if requested and credentials available
    if prefer_engine == "google" and os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
        return GoogleSearcher()

    if prefer_engine == "speedbird" and (os.getenv("Speedbird_SEARCH_API_KEY") or os.getenv("Speedbird_SEARCH_ENDPOINT")):
        return SpeedbirdSearcher()
    # Default fallback
    return WebSearcher()
