"""
论文来源管理模块 - 管理多个论文来源
"""
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import requests
from datetime import datetime


class PaperSource(ABC):
    """论文来源抽象基类"""
    
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """搜索论文"""
        pass
    
    @abstractmethod
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """获取论文详情"""
        pass


class ArxivSource(PaperSource):
    """arXiv 论文源"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """从 arXiv 搜索论文"""
        try:
            params = {
                "search_query": query,
                "start": 0,
                "max_results": top_k,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            return papers
        except Exception as e:
            print(f"arXiv 搜索失败: {e}")
            return []
    
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """获取 arXiv 论文详情"""
        try:
            params = {"search_query": f"arxiv:{paper_id}", "max_results": 1}
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            return papers[0] if papers else None
        except Exception as e:
            print(f"获取 arXiv 论文失败: {e}")
            return None
    
    @staticmethod
    def _parse_arxiv_response(response_text: str) -> List[Dict]:
        """解析 arXiv API 响应"""
        # 简化的 XML 解析（实际应该使用 xml.etree）
        papers = []
        # 这是一个占位符实现
        return papers


class SemanticScholarSource(PaperSource):
    """Semantic Scholar 论文源"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化"""
        self.api_key = api_key
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """从 Semantic Scholar 搜索论文"""
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
            print(f"Semantic Scholar 搜索失败: {e}")
            return []
    
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """获取论文详情"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        try:
            params = {"fields": "paperId,title,authors,abstract,url,year"}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._format_paper(data)
        except Exception as e:
            print(f"获取论文失败: {e}")
            return None
    
    @staticmethod
    def _parse_response(data: Dict) -> List[Dict]:
        """解析响应"""
        papers = []
        for item in data.get("data", []):
            paper = SemanticScholarSource._format_paper(item)
            if paper:
                papers.append(paper)
        return papers
    
    @staticmethod
    def _format_paper(item: Dict) -> Optional[Dict]:
        """格式化论文信息"""
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
    """Hugging Face Models 论文源"""
    
    BASE_URL = "https://huggingface.co/api"
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """搜索 Hugging Face 模型"""
        try:
            # 搜索模型而不是论文
            url = f"{self.BASE_URL}/models"
            params = {"search": query, "sort": "downloads", "limit": top_k}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            models = response.json()
            papers = self._format_models(models)
            return papers
        except Exception as e:
            print(f"Hugging Face 搜索失败: {e}")
            return []
    
    def fetch_paper(self, paper_id: str) -> Optional[Dict]:
        """获取模型详情"""
        try:
            url = f"{self.BASE_URL}/models/{paper_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            model = response.json()
            return self._format_model(model)
        except Exception as e:
            print(f"获取模型信息失败: {e}")
            return None
    
    @staticmethod
    def _format_models(models: List[Dict]) -> List[Dict]:
        """格式化模型列表"""
        papers = []
        for model in models:
            paper = HuggingFaceSource._format_model(model)
            if paper:
                papers.append(paper)
        return papers
    
    @staticmethod
    def _format_model(model: Dict) -> Optional[Dict]:
        """格式化单个模型"""
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
    """论文源管理器"""
    
    def __init__(self):
        """初始化"""
        self.sources: Dict[str, PaperSource] = {
            "arxiv": ArxivSource(),
            "semantic_scholar": SemanticScholarSource(),
            "huggingface": HuggingFaceSource(),
        }
    
    def register_source(self, name: str, source: PaperSource):
        """注册新的论文源"""
        self.sources[name] = source
    
    def search_all(self, query: str, top_k: int = 10) -> Dict[str, List[Dict]]:
        """在所有论文源中搜索"""
        results = {}
        for source_name, source in self.sources.items():
            try:
                papers = source.search(query, top_k=top_k)
                results[source_name] = papers
            except Exception as e:
                print(f"{source_name} 搜索失败: {e}")
                results[source_name] = []
        
        return results
    
    def search_specific(self, source_name: str, query: str, top_k: int = 10) -> List[Dict]:
        """在特定论文源中搜索"""
        source = self.sources.get(source_name)
        if not source:
            print(f"未找到论文源: {source_name}")
            return []
        
        return source.search(query, top_k=top_k)
