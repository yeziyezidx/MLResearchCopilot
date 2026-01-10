"""
论文信息抽取模块 - 从论文中抽取结构化信息
"""
from typing import Dict, List, Optional
from .structured_output import StructuredPaper
from .metadata import Method, Result, Citation


class PaperExtractor:
    """论文信息抽取器"""
    
    def __init__(self, llm_client=None):
        """
        初始化论文抽取器
        
        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
    
    def extract(self, paper: Dict) -> StructuredPaper:
        """
        从论文中抽取结构化信息
        
        Args:
            paper: 论文信息字典
            
        Returns:
            StructuredPaper: 结构化论文对象
        """
        # 基本信息
        structured = StructuredPaper(
            paper_id=paper.get("paper_id", ""),
            title=paper.get("title", ""),
            authors=paper.get("authors", []),
            abstract=paper.get("abstract", ""),
            url=paper.get("url", ""),
            source=paper.get("source", "unknown"),
            published_date=paper.get("published_date"),
            venue=paper.get("venue"),
            doi=paper.get("doi"),
            citations_count=paper.get("citations_count", 0),
        )
        
        # 如果有 LLM 客户端，使用 LLM 进行更深度的抽取
        if self.llm_client and paper.get("full_text"):
            extracted_info = self._extract_with_llm(paper)
            self._populate_extracted_info(structured, extracted_info)
        else:
            # 简单的本地抽取
            self._populate_simple_extraction(structured, paper)
        
        return structured
    
    def _extract_with_llm(self, paper: Dict) -> Dict:
        """使用 LLM 进行深度抽取"""
        prompt = self._build_extraction_prompt(paper)
        response = self.llm_client.call(prompt, output_format="json")
        return self._parse_extraction_response(response)
    
    def _build_extraction_prompt(self, paper: Dict) -> str:
        """构建提示词"""
        prompt = f"""请从以下论文中抽取结构化信息:

标题: {paper.get('title', '')}
摘要: {paper.get('abstract', '')}

{'全文: ' + paper.get('full_text', '')[:2000] if paper.get('full_text') else ''}

请提供以下结构化信息（JSON 格式）:
1. research_problem: 论文研究的主要问题
2. research_objectives: 研究目标列表
3. methods: 使用的方法列表（包含方法名称和描述）
4. datasets: 使用的数据集列表
5. results: 主要结果（指标和数值）
6. contributions: 主要贡献和创新点
7. limitations: 论文的局限性
8. future_work: 未来工作建议
9. keywords: 关键词列表
"""
        return prompt
    
    def _parse_extraction_response(self, response: str) -> Dict:
        """解析 LLM 响应"""
        # 简化的实现，实际应该使用 JSON 解析
        return {
            "research_problem": "",
            "research_objectives": [],
            "methods": [],
            "datasets": [],
            "results": [],
            "contributions": [],
            "limitations": [],
            "future_work": [],
            "keywords": [],
        }
    
    def _populate_extracted_info(self, structured: StructuredPaper, info: Dict):
        """填充 LLM 抽取的信息"""
        structured.research_problem = info.get("research_problem")
        structured.research_objectives = info.get("research_objectives", [])
        structured.datasets = info.get("datasets", [])
        structured.contributions = info.get("contributions", [])
        structured.limitations = info.get("limitations", [])
        structured.future_work = info.get("future_work", [])
        structured.keywords = info.get("keywords", [])
        
        # 处理方法
        methods_data = info.get("methods", [])
        for method_data in methods_data:
            if isinstance(method_data, dict):
                structured.methods.append(Method(
                    name=method_data.get("name", ""),
                    description=method_data.get("description", ""),
                ))
        
        # 处理结果
        results_data = info.get("results", [])
        for result_data in results_data:
            if isinstance(result_data, dict):
                structured.results.append(Result(
                    metric=result_data.get("metric", ""),
                    value=float(result_data.get("value", 0)),
                    dataset=result_data.get("dataset"),
                ))
    
    def _populate_simple_extraction(self, structured: StructuredPaper, paper: Dict):
        """简单的本地抽取"""
        # 从摘要中提取关键词
        abstract = paper.get("abstract", "")
        keywords = self._extract_keywords_simple(abstract)
        structured.keywords = keywords
        
        # 简单的问题抽取
        if "problem" in abstract.lower() or "challenge" in abstract.lower():
            sentences = abstract.split(".")
            structured.research_problem = sentences[0] if sentences else ""
    
    @staticmethod
    def _extract_keywords_simple(text: str) -> List[str]:
        """简单的关键词抽取"""
        # 这是一个非常简单的实现
        words = text.split()
        return [w for w in words if len(w) > 5][:10]
