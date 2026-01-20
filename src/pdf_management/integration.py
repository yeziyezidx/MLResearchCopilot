"""
PDF Integration Adapter - Integrates PDF processing into the main workflow
"""
from typing import List, Dict, Optional
from src.core.types import StructuredPaper
from src.pdf_management import PDFProcessor, ExtractedInfo


class PDFIntegrationAdapter:
    """PDF Integration Adapter - Connects PDF processing with the main workflow"""
    
    def __init__(self, llm_client=None, cache_dir: str = "./cache/pdfs"):
        """
        Initializes the integration adapter
        
        Args:
            llm_client: LLM client
            cache_dir: PDF cache directory
        """
        self.processor = PDFProcessor(
            cache_dir=cache_dir,
            llm_client=llm_client,
        )
        self.llm_client = llm_client
    
    def enrich_paper_with_pdf(
        self,
        paper: Dict,
        extract_pdf: bool = True,
    ) -> Dict:
        """
        Enriches paper information with PDF content
        
        Args:
            paper: Paper dictionary
            extract_pdf: Whether to extract PDF content
            
        Returns:
            Dict: Enriched paper information
        """
        if not extract_pdf or not paper.get("url"):
            return paper
        
        try:
            # Process PDF
            result = self.processor.process_paper(paper)
            
            if result["success"]:
                extracted = result.get("extracted_info")
                
                # Update paper information with PDF content
                paper["pdf_content"] = {
                    "full_text": self._extract_text_from_pdf(result["pdf_path"]),
                    "sections": {
                        "abstract": extracted.abstract if extracted else "",
                        "methodology": extracted.methodology if extracted else "",
                        "results": extracted.results if extracted else "",
                        "conclusion": extracted.conclusion if extracted else "",
                    },
                    "citations": result.get("citations", []),
                }
                paper["pdf_path"] = result["pdf_path"]
                paper["pdf_processed"] = True
            else:
                paper["pdf_error"] = result.get("error")
        
        except Exception as e:
            paper["pdf_error"] = str(e)
        
        return paper
    
    def enrich_papers_batch(
        self,
        papers: List[Dict],
        extract_pdf: bool = True,
    ) -> List[Dict]:
        """
        Enriches paper information in batch
        
        Args:
            papers: List of papers
            extract_pdf: Whether to extract PDF content
            
        Returns:
            List[Dict]: List of enriched papers
        """
        enriched = []
        
        for paper in papers:
            enriched_paper = self.enrich_paper_with_pdf(paper, extract_pdf)
            enriched.append(enriched_paper)
        
        return enriched
    
    @staticmethod
    def _extract_text_from_pdf(pdf_path: str) -> str:
        """Extracts all text from PDF"""
        try:
            import PyPDF2
            
            text = []
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            
            return "\n".join(text)
        
        except Exception as e:
            return f"[PDF text extraction failed: {e}]"
    
    def generate_synthesis_from_pdf(
        self,
        paper: Dict,
        synthesis_prompt: Optional[str] = None,
    ) -> str:
        """
        Generates a comprehensive summary from PDF content
        
        Args:
            paper: Paper dictionary (must include pdf_content)
            synthesis_prompt: Synthesis prompt
            
        Returns:
            str: LLM generated summary
        """
        if not self.llm_client:
            return "LLM client not configured"
        
        if not paper.get("pdf_content"):
            return "Paper PDF content not available"
        
        pdf_content = paper["pdf_content"]
        
        # Prepare content
        content_text = f"""
Paper Title: {paper.get('title', 'N/A')}

Abstract:
{pdf_content.get('sections', {}).get('abstract', '')[:500]}

Methodology:
{pdf_content.get('sections', {}).get('methodology', '')[:500]}

Main Results:
{pdf_content.get('sections', {}).get('results', '')[:500]}

Conclusion:
{pdf_content.get('sections', {}).get('conclusion', '')[:500]}
"""
        
        # Generate prompt
        if not synthesis_prompt:
            synthesis_prompt = """Based on the following paper content, please generate a detailed research summary, including:
1. Core problem and innovation points of the research
2. Main methods and techniques used
3. Key research results and findings
4. Potential applications and impacts
5. Differences from related work

Please answer in English, summary length 200-300 words."""
        
        prompt = f"""{synthesis_prompt}

Paper Content:
{content_text}
"""
        
        try:
            response = self.llm_client.call(prompt)
            return response
        except Exception as e:
            return f"Generation failed: {e}"
    
    def get_cache_stats(self) -> Dict:
        """Gets cache statistics"""
        return self.processor.get_cache_stats()
