"""
语义检索模块 - 基于向量相似度的论文检索
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class SearchResult:
    """搜索结果"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    source: str  # arXiv, ACL, GitHub, etc.
    score: float  # 相似度分数
    published_date: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
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
    """语义搜索模块"""
    
    def __init__(self, embedding_model=None):
        """
        初始化语义搜索器
        
        Args:
            embedding_model: 向量嵌入模型
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
        基于语义相似度搜索
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回top k结果
            
        Returns:
            List[Tuple]: [(文档索引, 相似度分数)]
        """
        # 获取查询的嵌入向量
        query_embedding = self._get_embedding(query)
        
        # 计算与所有文档的相似度
        similarities = []
        for idx, doc in enumerate(documents):
            doc_text = doc.get("title", "") + " " + doc.get("abstract", "")
            doc_embedding = self._get_embedding(doc_text)
            
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((idx, similarity))
        
        # 按相似度排序并返回 top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本的嵌入向量"""
        if self.embedding_model:
            return self.embedding_model.encode(text)
        else:
            # 简单的 TF-IDF 替代实现
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """简单的嵌入实现（用于演示）"""
        # 这是一个极简化的实现
        words = text.lower().split()
        vector = np.zeros(100)
        for word in words[:100]:
            if word:
                vector[hash(word) % 100] += 1
        return vector / (np.linalg.norm(vector) + 1e-8)
    
    @staticmethod
    def _cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        return float(dot_product / (norm_v1 * norm_v2))
