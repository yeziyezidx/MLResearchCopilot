"""
论文元数据定义
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Author:
    """作者信息"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Method:
    """方法信息"""
    name: str
    description: str
    parameters: Dict[str, str] = None


@dataclass
class Result:
    """结果信息"""
    metric: str  # 评估指标
    value: float
    dataset: Optional[str] = None


@dataclass
class Citation:
    """引用信息"""
    cited_paper_id: str
    cited_title: str
    context: str  # 引用的上下文


class PaperMetadata:
    """论文元数据"""
    
    REQUIRED_FIELDS = [
        "paper_id",
        "title",
        "authors",
        "abstract",
    ]
    
    OPTIONAL_FIELDS = [
        "publication_date",
        "venue",
        "url",
        "doi",
        "citations_count",
        "tags",
        "keywords",
    ]
    
    EXTRACTION_FIELDS = [
        "research_problem",
        "methods",
        "datasets",
        "results",
        "contributions",
        "limitations",
        "future_work",
    ]
    
    @staticmethod
    def get_all_fields() -> List[str]:
        """获取所有字段"""
        return PaperMetadata.REQUIRED_FIELDS + PaperMetadata.OPTIONAL_FIELDS + PaperMetadata.EXTRACTION_FIELDS
    
    @staticmethod
    def validate(data: Dict) -> bool:
        """验证必需字段"""
        for field in PaperMetadata.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                return False
        return True
