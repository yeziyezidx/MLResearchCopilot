"""
Structured paper output
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from .metadata import Method, Result, Citation


@dataclass
class StructuredPaper:
    """Structured paper"""
    
    # Basic information
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    source: str
    published_date: Optional[str] = None
    
    # Structured extraction of paper content
    research_problem: Optional[str] = None
    research_objectives: List[str] = field(default_factory=list)
    
    # Methods
    methods: List[Method] = field(default_factory=list)
    
    # Datasets
    datasets: List[str] = field(default_factory=list)
    
    # Experimental results
    results: List[Result] = field(default_factory=list)
    
    # Contributions and innovations
    contributions: List[str] = field(default_factory=list)
    
    # Limitations
    limitations: List[str] = field(default_factory=list)
    
    # Related work
    related_work: List[Citation] = field(default_factory=list)
    
    # Future work
    future_work: List[str] = field(default_factory=list)
    
    # Tags and keywords
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Metadata
    citations_count: int = 0
    venue: Optional[str] = None
    doi: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Converts to dictionary"""
        data = asdict(self)
        return data
    
    def to_table_row(self) -> Dict:
        """Converts to a table row (for display)"""
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
        """Formats results"""
        if not self.results:
            return "N/A"
        
        result_strs = [f"{r.metric}: {r.value}" for r in self.results[:3]]
        return "; ".join(result_strs)
