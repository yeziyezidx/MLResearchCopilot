"""
retriever - including multi retrieval approach
"""
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from .semantic_search import SemanticSearcher
from .paper_sources import PaperSourceManager
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class Retriever:
    """main retriever"""
    
    def __init__(self, use_semantic_search: bool = True, embedding_client = None):
        """
        initailize
        
        Args:
            use_semantic_search: if use semantic search
        """
        self.source_manager = PaperSourceManager()
        self.semantic_searcher = SemanticSearcher() if use_semantic_search else None
        self.embedding_client = embedding_client
    
    def _deduplicate_by_similarity(self, papers: List[Dict], key: str, threshold: float = 0.95):
        # 5.1. embedding-based deduplication
        print("\n-- step 5.1: paper deduplication...")
        paper_texts_to_embed = [p.get(key) for p in papers]
        embeddings = self.embedding_client.get_embeddings(paper_texts_to_embed)
        
        unique_papers = []
        if embeddings and any(e for e in embeddings):
            similarity_matrix = cosine_similarity(np.array(embeddings))
            to_keep = np.ones(len(papers), dtype=bool)
            for i in range(len(papers)):
                if to_keep[i]:
                    # if this paper is kept, mark all highly similar papers for removal
                    for j in range(i + 1, len(papers)):
                        if similarity_matrix[i, j] > threshold: # similarity threshold
                            to_keep[j] = False
            
            unique_papers = [papers[i] for i, keep in enumerate(to_keep) if keep]
            print(f" -> {len(papers) - len(unique_papers)} duplicate papers removed.")
        else:
            unique_papers = papers # skip deduplication if embeddings failed
        
        print(f" -> {len(unique_papers)} unique papers remaining.")
        return unique_papers
    
    def _deduplicate(self, papers: List[Dict], key: str) -> List[Dict]:
        seen = set()
        deduped_papers = []
        for paper in papers:
            value = paper.get(key)
            if value and value not in seen:
                seen.add(value)
                deduped_papers.append(paper)
        return deduped_papers

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
            query_papers = self._deduplicate(query_papers, "url")
            query_papers = self._deduplicate(query_papers, "title")
            if self.embedding_client:
                query_papers = self._deduplicate_by_similarity(query_papers, "title")
            
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
        final_papers = self._deduplicate(merged_top_papers, "url")
        final_papers = self._deduplicate(final_papers, "title")
        if self.embedding_client:
            final_papers = self._deduplicate_by_similarity(final_papers, "title")
        
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
