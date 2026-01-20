"""
retriever - including multi retrieval approach
"""
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from .semantic_search import SemanticSearcher
from .paper_sources import PaperSourceManager


class Retriever:
    """main retriever"""
    
    def __init__(self, use_semantic_search: bool = True):
        """
        initailize
        
        Args:
            use_semantic_search: if use semantic search
        """
        self.source_manager = PaperSourceManager()
        self.semantic_searcher = SemanticSearcher() if use_semantic_search else None
    
    def search(
        self,
        original_query: str,
        queries: List[str],
        top_k: int = 10,
        sources: Optional[List[str]] = None,
    ) -> Dict:
        """
        retrieve paper by query list and rank with a two-stage BM25 approach
        
        Args:
            original_query: The main query from the user.
            queries: A list of sub-queries (can include the original query).
            top_k: The final number of results to return.
            sources: paper domain source (search all if None)
            
        Returns:
            Dict: list of search result
        """
        
        def _deduplicate(papers: List[Dict], key: str) -> List[Dict]:
            seen = set()
            deduped_papers = []
            for paper in papers:
                value = paper.get(key)
                if value and value not in seen:
                    seen.add(value)
                    deduped_papers.append(paper)
            return deduped_papers

        if sources is None:
            sources = ["arxiv", "semantic_scholar"]

        merged_top_papers = []
        return_result = {"sub_query": {}, "original_query": []}
        
        # 1. Per-subquery processing
        for query in queries:
            # a. Retrieve documents
            query_papers = []
            for source in sources:
                papers = self.source_manager.search_specific(source, query, top_k=top_k) # Fetch more to have enough after dedup
                query_papers.extend(papers)
            
            # b. Deduplicate by url, then title
            query_papers = _deduplicate(query_papers, "url")
            query_papers = _deduplicate(query_papers, "title")
            
            if not query_papers:
                continue

            # c. Calculate BM25 scores against the subquery
            corpus = [(p.get("title", "") + " " + p.get("abstract", "")).lower() for p in query_papers]
            tokenized_corpus = [doc.split(" ") for doc in corpus]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.lower().split(" ")
            doc_scores = bm25.get_scores(tokenized_query)

            for paper, score in zip(query_papers, doc_scores):
                paper["score_bm25"] = score
            
            # d. Sort and take top 5
            query_papers.sort(key=lambda x: x.get("score_bm25", 0.0), reverse=True)
            merged_top_papers.extend(query_papers.copy())

            return_result["sub_query"][query] = query_papers
        
        # 2. Merge and Final Ranking
        # a. Deduplicate merged list by url, then title
        final_papers = _deduplicate(merged_top_papers, "url")
        final_papers = _deduplicate(final_papers, "title")

        if not final_papers:
            return return_result

        # b. Calculate final BM25 scores against the original_query
        corpus = [(p.get("title", "") + " " + p.get("abstract", "")).lower() for p in final_papers]
        tokenized_corpus = [doc.split(" ") for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = original_query.lower().split(" ")
        final_scores = bm25.get_scores(tokenized_query)

        # c. Create SearchResult objects
        for paper, score in zip(final_papers, final_scores):
            paper["score_bm25"] = score

        # d. Sort and return top_k
        final_papers.sort(key=lambda x: x.get("score_bm25", 0.0), reverse=True)
        return_result["original_query"] = final_papers

        return return_result
