"""
综合检索器 - 整合多个检索方法
"""
from typing import List, Dict, Optional
from .semantic_search import SemanticSearcher, SearchResult
from .paper_sources import PaperSourceManager


class Retriever:
    """综合检索器"""
    
    def __init__(self, use_semantic_search: bool = True):
        """
        初始化检索器
        
        Args:
            use_semantic_search: 是否使用语义搜索
        """
        self.source_manager = PaperSourceManager()
        self.semantic_searcher = SemanticSearcher() if use_semantic_search else None
    
    def search(
        self,
        queries: List[str],
        top_k: int = 10,
        sources: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        搜索相关论文
        
        Args:
            queries: 搜索查询列表
            top_k: 返回 top k 结果
            sources: 指定搜索的论文源 (如果为 None，则搜索所有源)
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        all_papers = {}
        
        # 从各个论文源搜索
        if sources is None:
            sources = ["arxiv", "semantic_scholar"]
        
        for source in sources:
            for query in queries:
                papers = self.source_manager.search_specific(source, query, top_k=top_k)
                for paper in papers:
                    paper_id = paper.get("paper_id", "")
                    if paper_id not in all_papers:
                        all_papers[paper_id] = paper
        
        # 转换为 SearchResult 对象
        results = []
        for paper in all_papers.values():
            result = SearchResult(
                paper_id=paper.get("paper_id", ""),
                title=paper.get("title", ""),
                authors=paper.get("authors", []),
                abstract=paper.get("abstract", ""),
                url=paper.get("url", ""),
                source=paper.get("source", "unknown"),
                score=paper.get("score", 0.0),
                published_date=paper.get("published_date"),
            )
            results.append(result)
        
        # 按相似度排序并返回 top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def search_by_keywords(
        self,
        keywords: List[str],
        top_k: int = 10,
    ) -> List[SearchResult]:
        """
        根据关键词搜索
        
        Args:
            keywords: 关键词列表
            top_k: 返回 top k 结果
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        # 组合关键词为搜索查询
        queries = [" ".join(keywords)] + keywords
        return self.search(queries, top_k=top_k)
