"""
跨论文聚合模块
"""
from typing import List, Dict, Optional
from collections import defaultdict
from src.extraction.structured_output import StructuredPaper


class Aggregator:
    """跨论文聚合器"""
    
    def __init__(self):
        """初始化聚合器"""
        pass
    
    def aggregate_methods(self, papers: List[StructuredPaper]) -> Dict[str, int]:
        """
        聚合所有论文中使用的方法
        
        Args:
            papers: 论文列表
            
        Returns:
            Dict: 方法频度统计
        """
        method_count = defaultdict(int)
        
        for paper in papers:
            for method in paper.methods:
                method_count[method.name] += 1
        
        return dict(sorted(method_count.items(), key=lambda x: x[1], reverse=True))
    
    def aggregate_datasets(self, papers: List[StructuredPaper]) -> Dict[str, int]:
        """
        聚合所有论文中使用的数据集
        
        Args:
            papers: 论文列表
            
        Returns:
            Dict: 数据集频度统计
        """
        dataset_count = defaultdict(int)
        
        for paper in papers:
            for dataset in paper.datasets:
                dataset_count[dataset] += 1
        
        return dict(sorted(dataset_count.items(), key=lambda x: x[1], reverse=True))
    
    def aggregate_metrics(self, papers: List[StructuredPaper]) -> Dict[str, List[float]]:
        """
        聚合所有论文中的评估指标
        
        Args:
            papers: 论文列表
            
        Returns:
            Dict: 指标值列表
        """
        metrics = defaultdict(list)
        
        for paper in papers:
            for result in paper.results:
                metrics[result.metric].append(result.value)
        
        return dict(metrics)
    
    def aggregate_keywords(self, papers: List[StructuredPaper]) -> Dict[str, int]:
        """
        聚合所有论文中的关键词
        
        Args:
            papers: 论文列表
            
        Returns:
            Dict: 关键词频度统计
        """
        keyword_count = defaultdict(int)
        
        for paper in papers:
            for keyword in paper.keywords:
                keyword_count[keyword.lower()] += 1
        
        return dict(sorted(keyword_count.items(), key=lambda x: x[1], reverse=True))
    
    def aggregate_contributions(self, papers: List[StructuredPaper]) -> List[Dict]:
        """
        聚合所有论文的贡献
        
        Args:
            papers: 论文列表
            
        Returns:
            List: 贡献列表（带来源信息）
        """
        contributions = []
        
        for paper in papers:
            for contribution in paper.contributions:
                contributions.append({
                    "contribution": contribution,
                    "paper_id": paper.paper_id,
                    "paper_title": paper.title,
                    "paper_url": paper.url,
                })
        
        return contributions
    
    def generate_summary(self, papers: List[StructuredPaper]) -> Dict:
        """
        生成论文集合的汇总统计
        
        Args:
            papers: 论文列表
            
        Returns:
            Dict: 汇总信息
        """
        return {
            "total_papers": len(papers),
            "top_methods": self.aggregate_methods(papers),
            "top_datasets": self.aggregate_datasets(papers),
            "metrics": self.aggregate_metrics(papers),
            "top_keywords": self.aggregate_keywords(papers),
            "contributions": self.aggregate_contributions(papers),
            "avg_citations": sum(p.citations_count for p in papers) / len(papers) if papers else 0,
        }
