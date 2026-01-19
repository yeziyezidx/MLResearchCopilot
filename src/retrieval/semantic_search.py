"""
semantic search - search according to vector similarity
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class SearchResult:
    """search result"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    source: str  # arXiv, ACL, GitHub, etc.
    score: float  # similarity score
    published_date: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """convert to dict"""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "source": self.source,
            "score": float(self.score),
            "published_date": self.published_date,
        }


class SemanticSearcher:
    """semantic search module"""
    
    def __init__(self, embedding_model=None):
        """
        initialize the semantic seacher
        
        Args:
            embedding_model: mebedding module
        """
        self.embedding_model = embedding_model
        self.document_cache: Dict[str, np.ndarray] = {}
    
    def search(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        search based on query vector and doc vector
        
        Args:
            query: search query
            documents: doc candidate list
            top_k: return top k result
            
        Returns:
            List[Tuple]: [(doc index, similarity score)]
        """
        # get the query embedding
        query_embedding = self._get_embedding(query)
        
        # compute the doc embedding
        similarities = []
        for idx, doc in enumerate(documents):
            doc_text = doc.get("title", "") + " " + doc.get("abstract", "")
            doc_embedding = self._get_embedding(doc_text)
            
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((idx, similarity))
        
        # ranking by similarity score and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """get doc embedding"""
        if self.embedding_model:
            return self.embedding_model.encode(text)
        else:
            # simple embedding by tf-idf
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """simple embedding demo"""
        # embedding demo 
        words = text.lower().split()
        vector = np.zeros(100)
        for word in words[:100]:
            if word:
                vector[hash(word) % 100] += 1
        return vector / (np.linalg.norm(vector) + 1e-8)
    
    @staticmethod
    def _cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """compute cosine similarity"""
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        return float(dot_product / (norm_v1 * norm_v2))
