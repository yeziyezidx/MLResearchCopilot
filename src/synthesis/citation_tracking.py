"""
引用溯源模块 - 进行句子级别的引用跟踪
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CitationEvidence:
    """引用证据"""
    sentence: str  # 引用的句子
    cited_paper_id: str  # 被引用论文 ID
    cited_title: str  # 被引用论文标题
    confidence: float  # 置信度 (0-1)


class CitationTracker:
    """引用溯源追踪器"""
    
    def __init__(self, llm_client=None):
        """
        初始化引用追踪器
        
        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
    
    def track_citations(self, sentence: str, candidate_papers: List[Dict]) -> List[CitationEvidence]:
        """
        追踪句子中的引用
        
        Args:
            sentence: 要分析的句子
            candidate_papers: 候选论文列表
            
        Returns:
            List[CitationEvidence]: 引用证据列表
        """
        citations = []
        
        for paper in candidate_papers:
            # 检查是否在句子中被提及
            if self._is_cited(sentence, paper):
                evidence = CitationEvidence(
                    sentence=sentence,
                    cited_paper_id=paper.get("paper_id", ""),
                    cited_title=paper.get("title", ""),
                    confidence=self._calculate_confidence(sentence, paper),
                )
                citations.append(evidence)
        
        return citations
    
    def _is_cited(self, sentence: str, paper: Dict) -> bool:
        """检查论文是否在句子中被引用"""
        title = paper.get("title", "").lower()
        authors = [a.lower() for a in paper.get("authors", [])]
        
        sentence_lower = sentence.lower()
        
        # 检查标题或作者名称
        if title in sentence_lower:
            return True
        
        for author in authors:
            if author in sentence_lower:
                return True
        
        return False
    
    def _calculate_confidence(self, sentence: str, paper: Dict) -> float:
        """计算引用置信度"""
        # 简化的置信度计算
        title = paper.get("title", "").lower()
        sentence_lower = sentence.lower()
        
        if title in sentence_lower:
            return 0.9
        
        authors = [a.lower() for a in paper.get("authors", [])]
        for author in authors:
            if author in sentence_lower:
                return 0.7
        
        return 0.3
    
    def extract_evidence_sentences(
        self,
        full_text: str,
        candidate_papers: List[Dict],
        context_window: int = 2,
    ) -> List[Dict]:
        """
        从全文中提取包含引用的句子
        
        Args:
            full_text: 论文全文
            candidate_papers: 候选论文列表
            context_window: 上下文窗口大小（句子数）
            
        Returns:
            List[Dict]: 证据句子及其上下文
        """
        sentences = full_text.split(".")
        evidence_list = []
        
        for idx, sentence in enumerate(sentences):
            citations = self.track_citations(sentence.strip(), candidate_papers)
            
            if citations:
                # 获取上下文
                start = max(0, idx - context_window)
                end = min(len(sentences), idx + context_window + 1)
                context = " ".join([s.strip() for s in sentences[start:end]])
                
                evidence_list.append({
                    "sentence": sentence.strip(),
                    "context": context,
                    "citations": [
                        {
                            "paper_id": c.cited_paper_id,
                            "paper_title": c.cited_title,
                            "confidence": c.confidence,
                        }
                        for c in citations
                    ],
                })
        
        return evidence_list
