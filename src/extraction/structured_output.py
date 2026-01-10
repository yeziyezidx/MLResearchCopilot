"""
结构化论文输出
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from .metadata import Method, Result, Citation


@dataclass
class StructuredPaper:
    """结构化论文"""
    
    # 基本信息
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    source: str
    published_date: Optional[str] = None
    
    # 论文内容的结构化抽取
    research_problem: Optional[str] = None
    research_objectives: List[str] = field(default_factory=list)
    
    # 方法
    methods: List[Method] = field(default_factory=list)
    
    # 数据集
    datasets: List[str] = field(default_factory=list)
    
    # 实验结果
    results: List[Result] = field(default_factory=list)
    
    # 贡献和创新点
    contributions: List[str] = field(default_factory=list)
    
    # 局限性
    limitations: List[str] = field(default_factory=list)
    
    # 相关工作
    related_work: List[Citation] = field(default_factory=list)
    
    # 未来工作
    future_work: List[str] = field(default_factory=list)
    
    # 标签和关键词
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # 元数据
    citations_count: int = 0
    venue: Optional[str] = None
    doi: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        return data
    
    def to_table_row(self) -> Dict:
        """转换为表格行（用于展示）"""
        return {
            "ID": self.paper_id,
            "Title": self.title,
            "Authors": ", ".join(self.authors),
            "Published": self.published_date or "Unknown",
            "Source": self.source,
            "Problem": self.research_problem or "N/A",
            "Methods": ", ".join([m.name for m in self.methods]) if self.methods else "N/A",
            "Results": self._format_results(),
            "Contributions": len(self.contributions),
            "URL": self.url,
        }
    
    def _format_results(self) -> str:
        """格式化结果"""
        if not self.results:
            return "N/A"
        
        result_strs = [f"{r.metric}: {r.value}" for r in self.results[:3]]
        return "; ".join(result_strs)
