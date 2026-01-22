"""
Cross-paper aggregation module
"""
from typing import List, Dict
from collections import defaultdict
from src.pdf_management.parser import ExtractedInfo
import numpy as np
from sklearn.cluster import KMeans
from string import Template

class Aggregator:
    """Cross-paper aggregator"""
    
    def __init__(self, llm_client=None):
        """Initializes the aggregator"""
        self.llm_client = llm_client

    def cluster_papers(self, papers: List[ExtractedInfo], embeddings: List[List[float]], num_clusters: int = 3) -> Dict[int, List[ExtractedInfo]]:
        """
        Clusters papers based on their embeddings.
        
        Args:
            papers: List of papers to cluster.
            embeddings: A list of embeddings corresponding to the papers.
            num_clusters: The number of clusters to create.
            
        Returns:
            A dictionary where keys are cluster IDs and values are lists of papers in that cluster.
        """
        if not papers or not embeddings or not any(e for e in embeddings):
            return {0: papers}

        num_clusters = min(len(papers), num_clusters)
        if num_clusters <= 0:
            return {0: papers}

        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(np.array(embeddings))
        
        clustered_papers = defaultdict(list)
        for paper, label in zip(papers, cluster_labels):
            clustered_papers[int(label)].append(paper)
        
        return dict(clustered_papers)
    
    def aggregate_methods(self, papers: List[ExtractedInfo]) -> Dict[str, int]:
        """
        Aggregates methods used across all papers
        
        Args:
            papers: List of papers
            
        Returns:
            Dict: Method frequency statistics
        """
        method_count = defaultdict(int)
        
        for paper in papers:
            for method in paper.methods:
                method_count[method.name] += 1
        
        return dict(sorted(method_count.items(), key=lambda x: x[1], reverse=True))
    
    def aggregate_datasets(self, papers: List[ExtractedInfo]) -> Dict[str, int]:
        """
        Aggregates datasets used across all papers
        
        Args:
            papers: List of papers
            
        Returns:
            Dict: Dataset frequency statistics
        """
        dataset_count = defaultdict(int)
        
        for paper in papers:
            for dataset in paper.datasets:
                dataset_count[dataset] += 1
        
        return dict(sorted(dataset_count.items(), key=lambda x: x[1], reverse=True))
    
    def aggregate_metrics(self, papers: List[ExtractedInfo]) -> Dict[str, List[float]]:
        """
        Aggregates evaluation metrics across all papers
        
        Args:
            papers: List of papers
            
        Returns:
            Dict: List of metric values
        """
        metrics = defaultdict(list)
        
        for paper in papers:
            for result in paper.results:
                metrics[result.metric].append(result.value)
        
        return dict(metrics)
    
    def aggregate_keywords(self, papers: List[ExtractedInfo]) -> Dict[str, int]:
        """
        Aggregates keywords across all papers
        
        Args:
            papers: List of papers
            
        Returns:
            Dict: Keyword frequency statistics
        """
        keyword_count = defaultdict(int)
        
        for paper in papers:
            for keyword in paper.keywords:
                keyword_count[keyword.lower()] += 1
        
        return dict(sorted(keyword_count.items(), key=lambda x: x[1], reverse=True))
    
    def aggregate_contributions(self, papers: List[ExtractedInfo]) -> List[Dict]:
        """
        Aggregates contributions from all papers
        
        Args:
            papers: List of papers
            
        Returns:
            List: List of contributions (with source information)
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

    def get_comparison_data(self, papers: List[ExtractedInfo]) -> List[Dict]:
        """
        Extracts data suitable for a comparative analysis table.
        """
        comparison_data = []
        for paper in papers:
            comparison_data.append({
                "title": paper.title,
                "objectives": paper.objectives,
                "methods": paper.methodology,
                "contributions": paper.contributions,
                "models": paper.models,
            })
        return comparison_data
    
    def generate_summary(self, papers: List[ExtractedInfo]) -> Dict:
        """
        Generates summary statistics for a collection of papers
        
        Args:
            papers: List of papers
            
        Returns:
            Dict: Summary information
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
