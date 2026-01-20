"""
Paper Information Extraction Module - Extracts structured information from papers
"""
from typing import Dict, List, Optional
from .structured_output import StructuredPaper
from .metadata import Method, Result, Citation


class PaperExtractor:
    """Paper Information Extractor"""
    
    def __init__(self, llm_client=None):
        """
        Initializes the paper extractor
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def extract(self, paper: Dict) -> StructuredPaper:
        """
        Extracts structured information from a paper
        
        Args:
            paper: Paper information dictionary
            
        Returns:
            StructuredPaper: Structured paper object
        """
        # Basic information
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
        
        # If an LLM client is available, use it for deeper extraction
        if self.llm_client and paper.get("full_text"):
            extracted_info = self._extract_with_llm(paper)
            self._populate_extracted_info(structured, extracted_info)
        else:
            # Simple local extraction
            self._populate_simple_extraction(structured, paper)
        
        return structured
    
    def _extract_with_llm(self, paper: Dict) -> Dict:
        """Performs deep extraction using LLM"""
        prompt = self._build_extraction_prompt(paper)
        response = self.llm_client.call(prompt, output_format="json")
        return self._parse_extraction_response(response)
    
    def _build_extraction_prompt(self, paper: Dict) -> str:
        """Builds the extraction prompt"""
        prompt = f"""Please extract structured information from the following paper:

Title: {paper.get('title', '')}
Abstract: {paper.get('abstract', '')}

{'Full text: ' + paper.get('full_text', '')[:2000] if paper.get('full_text') else ''}

Please provide the following structured information (in JSON format):
1. research_problem: The main problem the paper studies
2. research_objectives: List of research objectives
3. methods: List of methods used (including name and description)
4. datasets: List of datasets used
5. results: Main results (metrics and values)
6. contributions: Main contributions and innovations
7. limitations: Limitations of the paper
8. future_work: Suggestions for future work
9. keywords: List of keywords
"""
        return prompt
    
    def _parse_extraction_response(self, response: str) -> Dict:
        """Parses LLM response"""
        # Simplified implementation, should ideally use JSON parsing
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
        """Populates information extracted by LLM"""
        structured.research_problem = info.get("research_problem")
        structured.research_objectives = info.get("research_objectives", [])
        structured.datasets = info.get("datasets", [])
        structured.contributions = info.get("contributions", [])
        structured.limitations = info.get("limitations", [])
        structured.future_work = info.get("future_work", [])
        structured.keywords = info.get("keywords", [])
        
        # Process methods
        methods_data = info.get("methods", [])
        for method_data in methods_data:
            if isinstance(method_data, dict):
                structured.methods.append(Method(
                    name=method_data.get("name", ""),
                    description=method_data.get("description", ""),
                ))
        
        # Process results
        results_data = info.get("results", [])
        for result_data in results_data:
            if isinstance(result_data, dict):
                structured.results.append(Result(
                    metric=result_data.get("metric", ""),
                    value=float(result_data.get("value", 0)),
                    dataset=result_data.get("dataset"),
                ))
    
    def _populate_simple_extraction(self, structured: StructuredPaper, paper: Dict):
        """Simple local extraction"""
        # Extract keywords from abstract
        abstract = paper.get("abstract", "")
        keywords = self._extract_keywords_simple(abstract)
        structured.keywords = keywords
        
        # Simple problem extraction
        if "problem" in abstract.lower() or "challenge" in abstract.lower():
            sentences = abstract.split(".")
            structured.research_problem = sentences[0] if sentences else ""
    
    @staticmethod
    def _extract_keywords_simple(text: str) -> List[str]:
        """Simple keyword extraction"""
        # This is a very simple implementation
        words = text.split()
        return [w for w in words if len(w) > 5][:10]

