"""
问题构建模块 - 将用户问题转化为结构化的域问题
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DomainProblem:
    """域问题"""
    problem_statement: str
    research_objectives: List[str]
    evaluation_metrics: List[str]
    constraints: List[str]
    assumptions: List[str]
    search_queries: List[str]  # 用于检索的搜索查询
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "problem_statement": self.problem_statement,
            "research_objectives": self.research_objectives,
            "evaluation_metrics": self.evaluation_metrics,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
            "search_queries": self.search_queries,
        }


class ProblemFormulator:
    """问题构建模块"""
    
    def __init__(self, llm_client=None):
        """
        初始化问题构建器
        
        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
    
    def formulate(
        self,
        query: str,
        keywords: List[str],
        intent: Dict,
        context: Optional[str] = None,
    ) -> DomainProblem:
        """
        将用户问题转化为结构化的域问题
        
        Args:
            query: 原始用户问题
            keywords: 抽取的关键词
            intent: 研究意图
            context: 背景信息
            
        Returns:
            DomainProblem: 结构化的域问题
        """
        # 构建提示词
        prompt = self._build_prompt(query, keywords, intent, context)
        
        # 调用 LLM 进行结构化处理
        if self.llm_client:
            response = self.llm_client.call(prompt)
            problem_data = self._parse_response(response)
        else:
            problem_data = self._local_formulation(query, keywords)
        
        return DomainProblem(
            problem_statement=query,
            research_objectives=problem_data.get("research_objectives", [query]),
            evaluation_metrics=problem_data.get("evaluation_metrics", []),
            constraints=problem_data.get("constraints", []),
            assumptions=problem_data.get("assumptions", []),
            search_queries=problem_data.get("search_queries", keywords),
        )
    
    def _build_prompt(
        self,
        query: str,
        keywords: List[str],
        intent: Dict,
        context: Optional[str] = None,
    ) -> str:
        """构建提示词"""
        prompt = f"""基于以下信息，构建一个结构化的研究问题:

用户问题: {query}
关键词: {', '.join(keywords)}
研究领域: {intent.get('research_area', 'Machine Learning')}

请提供:
1. 研究目标 (3-5 个具体目标)
2. 评估指标 (如何评估成功)
3. 约束条件 (时间、资源等)
4. 基本假设
5. 用于文献检索的优化查询 (3-5 个)

请以结构化格式回复。
"""
        if context:
            prompt += f"\n背景信息: {context}"
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict:
        """解析 LLM 响应"""
        # 简单的解析实现
        return {
            "research_objectives": [response],
            "evaluation_metrics": [],
            "constraints": [],
            "assumptions": [],
            "search_queries": [],
        }
    
    def _local_formulation(self, query: str, keywords: List[str]) -> Dict:
        """本地问题构建"""
        return {
            "research_objectives": [query],
            "evaluation_metrics": ["准确性", "效率"],
            "constraints": [],
            "assumptions": [],
            "search_queries": keywords,
        }
