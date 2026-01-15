"""
problem formulation - convert user query to domain problem 
"""
from typing import Dict, List, Optional
from dataclasses import dataclass

from string import Template
import json

concept_understanding_template = Template(r'''

You are a senior research scientist and systems architect. 
                  
''')

@dataclass
class DomainProblem:
    """domain problem"""
    problem_statement: str
    research_objectives: List[str]
    evaluation_metrics: List[str]
    constraints: List[str]
    assumptions: List[str]
    search_queries: List[str]  # 用于检索的搜索查询
    
    def to_dict(self) -> Dict:
        return {
            "problem_statement": self.problem_statement,
            "research_objectives": self.research_objectives,
            "evaluation_metrics": self.evaluation_metrics,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
            "search_queries": self.search_queries,
        }


class ProblemFormulator:
    """ProblemFormulator"""
    
    def __init__(self, llm_client=None):
        """
        inialize the problem constructor
        
        Args:
            llm_client: LLM client
        """
        self.llm_client = llm_client
    
    def formulate(
        self,
        query: str,
        keywords: Dict,
        intent: Dict,
        context: Optional[str] = None,
    ) -> DomainProblem:
        """
        convert the user query into paper search - oriented query
        
        Args:
            query: initial query
            keywords: the domain concepts
            intent: query subintens
            context: background
            
        Returns:
            DomainProblem: stuctured domain problem
        """

        prompt = self._build_prompt(query, keywords, intent, context)
        

        if self.llm_client:
            response = self.llm_client.call(prompt, max_tokens=10240,output_format="json")
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
