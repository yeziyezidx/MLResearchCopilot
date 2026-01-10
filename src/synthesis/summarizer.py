"""
多文档综合总结模块
"""
from typing import List, Dict, Optional
from src.extraction.structured_output import StructuredPaper


class Summarizer:
    """多文档综合总结器"""
    
    def __init__(self, llm_client=None):
        """
        初始化总结器
        
        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
    
    def synthesize(self, papers: List[StructuredPaper]) -> Dict:
        """
        综合多篇论文进行总结
        
        Args:
            papers: 论文列表
            
        Returns:
            Dict: 综合总结结果
        """
        if not papers:
            return {"summary": "", "insights": []}
        
        # 收集信息
        paper_summaries = [self._summarize_paper(paper) for paper in papers]
        
        # 使用 LLM 进行交叉综合
        if self.llm_client:
            synthesis = self._synthesize_with_llm(papers, paper_summaries)
        else:
            synthesis = self._synthesize_local(papers, paper_summaries)
        
        return synthesis
    
    def _summarize_paper(self, paper: StructuredPaper) -> Dict:
        """总结单篇论文"""
        return {
            "title": paper.title,
            "paper_id": paper.paper_id,
            "research_problem": paper.research_problem,
            "key_methods": [m.name for m in paper.methods],
            "datasets": paper.datasets,
            "contributions": paper.contributions,
            "limitations": paper.limitations,
            "keywords": paper.keywords,
        }
    
    def _synthesize_with_llm(self, papers: List[StructuredPaper], summaries: List[Dict]) -> Dict:
        """使用 LLM 进行综合"""
        prompt = self._build_synthesis_prompt(papers, summaries)
        response = self.llm_client.call(prompt)
        
        return {
            "summary": response,
            "insights": self._extract_insights(response, papers),
            "consensus": self._identify_consensus(papers),
            "gaps": self._identify_gaps(papers),
            "future_directions": self._suggest_future_directions(papers),
        }
    
    def _synthesize_local(self, papers: List[StructuredPaper], summaries: List[Dict]) -> Dict:
        """本地综合（简化版）"""
        return {
            "summary": self._generate_local_summary(papers),
            "insights": self._identify_insights_local(papers),
            "consensus": self._identify_consensus(papers),
            "gaps": self._identify_gaps(papers),
            "future_directions": self._suggest_future_directions(papers),
        }
    
    def _build_synthesis_prompt(self, papers: List[StructuredPaper], summaries: List[Dict]) -> str:
        """构建综合提示词"""
        prompt = "基于以下论文进行多文档综合总结:\n\n"
        
        for summary in summaries[:5]:  # 最多 5 篇论文
            prompt += f"论文: {summary['title']}\n"
            prompt += f"问题: {summary['research_problem']}\n"
            prompt += f"方法: {', '.join(summary['key_methods'])}\n"
            prompt += f"贡献: {'; '.join(summary['contributions'][:2])}\n\n"
        
        prompt += """
请提供:
1. 综合总结 (200-300字)
2. 关键洞察和发现
3. 主要共识（所有论文一致的观点）
4. 存在的研究缺口
5. 未来研究方向建议
"""
        return prompt
    
    def _generate_local_summary(self, papers: List[StructuredPaper]) -> str:
        """生成本地总结"""
        if not papers:
            return ""
        
        summary = f"本综述包含 {len(papers)} 篇论文。\n\n"
        
        # 汇总研究问题
        problems = [p.research_problem for p in papers if p.research_problem]
        if problems:
            summary += f"主要研究问题: {'; '.join(set(problems[:3]))}\n\n"
        
        # 汇总方法
        all_methods = set()
        for paper in papers:
            for method in paper.methods:
                all_methods.add(method.name)
        if all_methods:
            summary += f"常用方法: {', '.join(list(all_methods)[:5])}\n\n"
        
        # 汇总数据集
        all_datasets = set()
        for paper in papers:
            all_datasets.update(paper.datasets)
        if all_datasets:
            summary += f"常用数据集: {', '.join(list(all_datasets)[:5])}\n"
        
        return summary
    
    def _extract_insights(self, synthesis: str, papers: List[StructuredPaper]) -> List[str]:
        """提取洞察"""
        # 简化实现
        return [
            "论文普遍关注方法效率的改进",
            "数据集的多样性是重要考虑因素",
            "评估指标需要更全面的定义",
        ]
    
    def _identify_consensus(self, papers: List[StructuredPaper]) -> Dict:
        """识别共识"""
        # 统计最常见的方法和数据集
        from collections import Counter
        
        all_methods = []
        all_datasets = []
        
        for paper in papers:
            for method in paper.methods:
                all_methods.append(method.name)
            all_datasets.extend(paper.datasets)
        
        return {
            "common_methods": Counter(all_methods).most_common(3),
            "common_datasets": Counter(all_datasets).most_common(3),
        }
    
    def _identify_gaps(self, papers: List[StructuredPaper]) -> List[str]:
        """识别研究缺口"""
        gaps = []
        
        all_limitations = []
        for paper in papers:
            all_limitations.extend(paper.limitations)
        
        # 统计最常见的局限性
        from collections import Counter
        if all_limitations:
            common_limitations = Counter(all_limitations).most_common(3)
            gaps = [limitation for limitation, count in common_limitations]
        
        return gaps
    
    def _suggest_future_directions(self, papers: List[StructuredPaper]) -> List[str]:
        """建议未来方向"""
        directions = []
        
        for paper in papers:
            directions.extend(paper.future_work)
        
        # 返回前 5 个建议
        return list(set(directions))[:5]
