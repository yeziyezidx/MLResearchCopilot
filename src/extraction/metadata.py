"""
Paper metadata definitions
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Author:
    """Author information"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Method:
    """Method information"""
    name: str
    description: str
    parameters: Dict[str, str] = None


@dataclass
class Result:
    """Result information"""
    metric: str  # Evaluation metric
    value: float
    dataset: Optional[str] = None


@dataclass
class Citation:
    """Citation information"""
    cited_paper_id: str
    cited_title: str
    context: str  # Context of the citation


class PaperMetadata:
    """Paper metadata"""
    
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
        """Gets all fields"""
        return PaperMetadata.REQUIRED_FIELDS + PaperMetadata.OPTIONAL_FIELDS + PaperMetadata.EXTRACTION_FIELDS
    
    @staticmethod
    def validate(data: Dict) -> bool:
        """Validates required fields"""
        for field in PaperMetadata.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                return False
        return True
