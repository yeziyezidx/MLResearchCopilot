"""
paper sources management - manage paper from multi-sources
"""
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import re
from src.core.web_search import get_searcher, SearchResult

class PaperSource(ABC):
    """paper sourcess"""
    
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """search paper by query"""
        pass
    
    @abstractmethod
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """fetch paper details by paper id"""
        pass


class ArxivSource(PaperSource):
    """arXiv paper source"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """search paper from arXiv source by query"""
        try:
            params = {
                "search_query": query,
                "start": 0,
                "max_results": top_k,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=60)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            return papers
        except Exception as e:
            print(f"arXiv search failed: {e}")
            return []
    
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """fetch paper detail from arXiv by paper id"""
        try:
            params = {"search_query": f"arxiv:{paper_id}", "max_results": 1}
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            return papers[0] if papers else None
        except Exception as e:
            print(f"fetch arXiv paper failed: {e}")
            return None

    @staticmethod
    def _parse_arxiv_response(response_text: str) -> List[Dict]:
        """parse arXiv API response"""
        papers = []
        try:
            root = ET.fromstring(response_text)
            
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                paper_id = None
                url = ""
                id_tag = entry.find('atom:id', ns)
                if id_tag is not None and id_tag.text:
                    url = id_tag.text
                    # Extract arxiv id from the URL
                    match = re.search(r'arxiv\.org/abs/(\d{4}\.\d{5}(v\d+)?)', id_tag.text)
                    if match:
                        paper_id = match.group(1)
                
                title = entry.find('atom:title', ns).text if entry.find('atom:title', ns) is not None else "N/A"
                summary = entry.find('atom:summary', ns).text if entry.find('atom:summary', ns) is not None else "N/A"
                published_date = entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else "N/A"
                
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns) if author.find('atom:name', ns) is not None]
                
                pdf_url = None
                # Arxiv provides multiple links, typically one with rel='alternate' for HTML and one with rel='related' and type='application/pdf' for PDF
                for link in entry.findall('atom:link', ns):
                    if 'title' in link.attrib and link.attrib['title'] == 'pdf':
                        pdf_url = link.attrib['href']
                        break
                
                papers.append({
                    "paper_id": paper_id,
                    "title": title.strip(),
                    "authors": authors,
                    "abstract": summary.strip(),
                    "url": url, 
                    "pdf_url": pdf_url, # Prioritize PDF link as the main URL
                    "source": "arxiv",
                    "published_date": published_date,
                })
        except ET.ParseError as e:
            print(f"Error parsing arXiv XML response: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during arXiv response parsing: {e}")
        return papers


class WebSource(PaperSource):
    """websearch paper source"""
    def __init__(self, prefer_engine: str = "speedbird"):
        """initialize"""
        self.searcher = get_searcher(prefer_engine = prefer_engine)

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """search paper from arXiv source by query"""
        try:
            search_results = self.searcher.search(query, top_k)
            papers = self._parse_web_papers(search_results)
            return papers
        except Exception as e:
            print(f"web search failed: {e}")
            return []
    
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """fetch paper detail from websearch by paper id"""
        print("not implemented")
        pass
    def _parse_web_papers(self, search_result: SearchResult):
        papers = []
        for result in search_result:
            try: 
                paper_id, pdf_url = None, None
                url = result.url
                # Extract arxiv id from the URL
                paper_id, pdf_url = self._parse_url_for_arxiv_id(url)
                
                # If not an arXiv paper, try to extract from HTML content
                if not pdf_url:
                    if url.endswith("pdf"):
                        pdf_url = url
                if not pdf_url:
                    try:
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        html_content = response.text
                        pdf_url = self._extract_pdf_info_from_html(html_content, url)
                    except requests.exceptions.RequestException as req_e:
                        print(f"Failed to fetch content from {url}: {req_e}")
                    except Exception as html_e:
                        print(f"Error parsing HTML from {url}: {html_e}")

                title = result.title
                summary = result.snippet
                published_date = "N/A"
                
                authors = []
                if pdf_url: 
                    papers.append({
                            "paper_id": paper_id,
                            "title": title.strip(),
                            "authors": authors,
                            "abstract": summary.strip(),
                            "url": url, 
                            "pdf_url": pdf_url, # Prioritize PDF link as the main URL
                            "source": "web",
                            "published_date": published_date,
                        })

            except Exception as e:
                print(f"An unexpected error occurred during web papere parsing: {e}")
        return papers

    def _parse_url_for_arxiv_id(self, url: str):
        """
        Parses a URL to extract an arXiv paper ID and constructs a PDF URL.
        Returns (paper_id, pdf_url) or (None, None) if not an arXiv URL.
        """
        # Regex to match arXiv URLs (abs, pdf, or html versions)
        # It handles both 'v' versions (e.g., 1234.56789v1) and non-'v' versions
        arxiv_id_match = re.search(r'(?:arxiv.org/(?:abs|pdf|html)/)(\d{4}.\d{5}(?:v\d+)?)', url)
        if arxiv_id_match:
            paper_id = arxiv_id_match.group(1)
            pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
            return paper_id, pdf_url
        return None, None

    def _is_pdf_url(self,url: str) -> bool:
        """
        Checks if a URL points directly to a PDF file.
        """
        return url.strip().lower().endswith('.pdf')
    
    @staticmethod
    def _extract_pdf_info_from_html(html_content: str, original_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts PDF URL and paper ID from HTML content for specific sources.
        Currently handles aclanthology.org.
        """
        pdf_url = None
        # Try to find PDF link
        # Common pattern for aclanthology.org: <a class="btn btn-primary btn-md" href="/pdf/...">PDF</a>
        pdf_match = re.search(r'href="(.*?\.pdf)"', html_content)
        if pdf_match:
            pdf_path = pdf_match.group(1)
            # aclanthology uses relative paths or full paths. Normalize to full URL.
            if pdf_path.startswith('/'):
                base_url = re.match(r'(https?://[^/]+)', original_url)
                if base_url:
                    pdf_url = base_url.group(1) + pdf_path
            else:
                # Assume it's a full URL or relative to the current path if no leading '/'
                pdf_url = pdf_path # Or potentially original_url + '/' + pdf_path if it's relative to the current path without leading slash


        return pdf_url
    
class SemanticScholarSource(PaperSource):
    """Semantic Scholar paper source"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """initialize"""
        self.api_key = api_key
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """search paper form Semantic Scholar"""
        try:
            params = {
                "query": query,
                "limit": top_k,
                "fields": "paperId,title,authors,abstract,url,year",
            }
            
            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            papers = self._parse_response(data)
            return papers
        except Exception as e:
            print(f"Semantic Scholar search failed: {e}")
            return []
    
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """fetch paper details"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        try:
            params = {"fields": "paperId,title,authors,abstract,url,year"}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._format_paper(data)
        except Exception as e:
            print(f"fetch paper failed: {e}")
            return None
    
    @staticmethod
    def _parse_response(data: Dict) -> List[Dict]:
        """parse response"""
        papers = []
        for item in data.get("data", []):
            paper = SemanticScholarSource._format_paper(item)
            if paper:
                papers.append(paper)
        return papers
    
    @staticmethod
    def _format_paper(item: Dict) -> Optional[Dict]:
        """format paper info"""
        if not item:
            return None
        
        return {
            "paper_id": item.get("paperId", ""),
            "title": item.get("title", ""),
            "authors": [a.get("name", "") for a in item.get("authors", [])],
            "abstract": item.get("abstract", ""),
            "url": item.get("url", ""),
            "source": "semantic_scholar",
            "published_date": str(item.get("year", "")),
        }


class HuggingFaceSource(PaperSource):
    """Hugging Face Models paper sources"""
    
    BASE_URL = "https://huggingface.co/api"
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """search model of Hugging Face"""
        try:
            # search models instead of paper
            url = f"{self.BASE_URL}/models"
            params = {"search": query, "sort": "downloads", "limit": top_k}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            models = response.json()
            papers = self._format_models(models)
            return papers
        except Exception as e:
            print(f"Hugging Face search failed: {e}")
            return []
    
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """fetch paper details"""
        try:
            url = f"{self.BASE_URL}/models/{paper_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            model = response.json()
            return self._format_model(model)
        except Exception as e:
            print(f"fetch model failed: {e}")
            return None
    
    @staticmethod
    def _format_models(models: List[Dict]) -> List[Dict]:
        """format model list"""
        papers = []
        for model in models:
            paper = HuggingFaceSource._format_model(model)
            if paper:
                papers.append(paper)
        return papers
    
    @staticmethod
    def _format_model(model: Dict) -> Optional[Dict]:
        """format single model"""
        if not model:
            return None
        
        return {
            "paper_id": model.get("id", ""),
            "title": model.get("id", ""),
            "authors": [model.get("author", "")],
            "abstract": model.get("description", ""),
            "url": f"https://huggingface.co/{model.get('id', '')}",
            "source": "huggingface",
            "published_date": model.get("created_at", ""),
        }


class PaperSourceManager:
    """paper source manager"""
    
    def __init__(self):
        """initialize"""
        self.sources: Dict[str, PaperSource] = {
            "arxiv": ArxivSource(),
            "semantic_scholar": SemanticScholarSource(),
            "huggingface": HuggingFaceSource(),
            "web": WebSource(),
        }
    
    def register_source(self, name: str, source: PaperSource):
        """register new source"""
        self.sources[name] = source
    
    def search_all(self, query: str, top_k: int = 10) -> Dict[str, List[Dict]]:
        """search in all sources"""
        results = {}
        for source_name, source in self.sources.items():
            try:
                papers = source.search(query, top_k=top_k)
                results[source_name] = papers
            except Exception as e:
                print(f"{source_name} search failed: {e}")
                results[source_name] = []
        
        return results
    
    def search_specific(self, source_name: str, query: str, top_k: int = 10) -> List[Dict]:
        """search in specific source"""
        source = self.sources.get(source_name)
        if not source:
            print(f"source not found: {source_name}")
            return []
        
        return source.search(query, top_k=top_k)
