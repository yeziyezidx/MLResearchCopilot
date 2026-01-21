"""
Multi-document comprehensive summarization module
"""
from typing import List, Dict, Optional
from src.pdf_management.parser import ExtractedInfo
from src.core.concept_understanding import ConceptDefinition

class Summarizer:
    """Multi-document comprehensive summarizer"""
    
    def __init__(self, llm_client=None):
        """
        Initializes the summarizer
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def synthesize(self, query, concepts: ConceptDefinition , papers: List[Dict]) -> Dict:
        """
        Synthesizes multiple papers into a summary
        
        Args:
            papers: List of papers
            
        Returns:
            Dict: Comprehensive summary results
        """
        if not papers:
            return {"summary": "", "insights": []}
        
        # Collect information
        paper_summaries = []
        for paper in papers:
            if paper["success"] and paper["extracted_info"]:
                paper_summaries.append(paper["extracted_info"])
        
        # Use LLM for cross-synthesis
        if self.llm_client:
            synthesis = self._synthesize_with_llm(papers, paper_summaries)
        else:
            synthesis = self._synthesize_local(papers, paper_summaries)
        
        return synthesis
    
    
    def _synthesize_with_llm(self, papers: List[ExtractedInfo], summaries: List[Dict]) -> Dict:
        """Performs synthesis using LLM"""
        prompt = self._build_synthesis_prompt(papers, summaries)
        response = self.llm_client.call(prompt)
        
        return {
            "summary": response,
            "insights": self._extract_insights(response, papers),
            "consensus": self._identify_consensus(papers),
            "gaps": self._identify_gaps(papers),
            "future_directions": self._suggest_future_directions(papers),
        }
    
    def _synthesize_local(self, papers: List[ExtractedInfo], summaries: List[Dict]) -> Dict:
        """Local synthesis (simplified)"""
        return {
            "summary": self._generate_local_summary(papers),
            "insights": self._identify_insights_local(papers),
            "consensus": self._identify_consensus(papers),
            "gaps": self._identify_gaps(papers),
            "future_directions": self._suggest_future_directions(papers),
        }
    
    def _build_synthesis_prompt(self, papers: List[ExtractedInfo], summaries: List[Dict]) -> str:
        """Builds the synthesis prompt"""
        prompt = "Perform multi-document comprehensive summarization based on the following papers:\n\n"
        
        for summary in summaries[:5]:  # Up to 5 papers
            prompt += f"Paper: {summary['title']}\n"
            prompt += f"Problem: {summary['research_problem']}\n"
            prompt += f"Method: {', '.join(summary['key_methods'])}\n"
            prompt += f"Contribution: {'; '.join(summary['contributions'][:2])}\n\n"
        
        prompt += """
Please provide:
1. Comprehensive summary (200-300 words)
2. Key insights and findings
3. Main consensus (views consistent across all papers)
4. Existing research gaps
5. Suggested future research directions
"""
        return prompt
    
    def _generate_local_summary(self, papers: List[ExtractedInfo]) -> str:
        """generate local summary"""
        if not papers:
            return ""
        
        summary = f"This summary including {len(papers)} papers\n\n"
        
        # summarize the research objectivs
        problems = [p.objectives for p in papers if p.objectives]
        if problems:
            summary += f"The main research problems: {'; '.join(set(problems[:3]))}\n\n"
        
        # summarize the methods
        all_methods = set()
        for paper in papers:
            method = paper.methodology
            all_methods.add(method)
        if all_methods:
            summary += f"The existing methods including: {', '.join(list(all_methods)[:5])}\n\n"
        
        # summarize the datasets
        all_datasets = set()
        for paper in papers:
            all_datasets.update(paper.datasets)
        if all_datasets:
            summary += f"it usually use the datasets: {', '.join(list(all_datasets)[:5])}\n"
        
        return summary
    
    def _extract_insights(self, synthesis: str, papers: List[ExtractedInfo]) -> List[str]:
        """extract insights"""
        # simple func
        return [
            "论文普遍关注方法效率的改进",
            "数据集的多样性是重要考虑因素",
            "评估指标需要更全面的定义",
        ]
    
    def _identify_consensus(self, papers: List[ExtractedInfo]) -> Dict:
        """identify consensus"""
        # the the common
        from collections import Counter
        
        all_methods = []
        all_datasets = []
        
        for paper in papers:
            method = paper.methodology
            all_methods.append(method)
            all_datasets.extend(paper.datasets)
        
        return {
            "common_methods": Counter(all_methods).most_common(3),
            "common_datasets": Counter(all_datasets).most_common(3),
        }
    
    def _identify_gaps(self, papers: List[ExtractedInfo]) -> List[str]:
        """identify the limitations"""
        gaps = []
        
        all_limitations = []
        for paper in papers:
            all_limitations.extend(paper.limitations)
        
        # get the common limitations
        from collections import Counter
        if all_limitations:
            common_limitations = Counter(all_limitations).most_common(3)
            gaps = [limitation for limitation, count in common_limitations]
        
        return gaps