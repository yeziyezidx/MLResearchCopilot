"""
PDF Parser - Supports text extraction, segmentation, and metadata parsing.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PDFPage:
    """PDF Page"""
    page_number: int
    text: str
    metadata: Dict = None


@dataclass
class PDFSection:
    """PDF Section"""
    title: str
    start_page: int
    end_page: int
    content: str
    subsections: List["PDFSection"] = None


@dataclass
class ExtractedInfo:
    """Extracted Information"""
    title: str
    authors: List[str]
    abstract: str
    methodology: str
    results: str
    conclusion: str
    figures: List[Dict]
    tables: List[Dict]


class PDFParser:
    """PDF Parser"""
    
    def __init__(self, llm_client=None):
        """
        Initializes the PDF parser
        
        Args:
            llm_client: LLM client (for intelligent parsing)
        """
        self.llm_client = llm_client
    
    def extract_text(self, pdf_path: str) -> List[PDFPage]:
        """
        Extracts text from a PDF
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            List[PDFPage]: List of PDF pages
        """
        try:
            import PyPDF2
        except ImportError:
            print("Warning: PyPDF2 not installed, using basic parsing")
            return self._basic_text_extraction(pdf_path)
        
        pages = []
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    
                    pages.append(PDFPage(
                        page_number=page_num,
                        text=text,
                        metadata={
                            "rotation": page.get("/Rotate", 0),
                            "media_box": page.mediabox,
                        }
                    ))
        
        except Exception as e:
            print(f"PDF extraction failed: {e}")
        
        return pages
    
    def _basic_text_extraction(self, pdf_path: str) -> List[PDFPage]:
        """Basic text extraction (when PyPDF2 is not available)"""
        # This is a fallback, should ideally use pdfplumber or PyPDF2
        return []
    
    def parse_structure(self, pages: List[PDFPage]) -> List[PDFSection]:
        """
        Parses PDF structure (identifies chapters)
        
        Args:
            pages: List of PDF pages
            
        Returns:
            List[PDFSection]: List of PDF sections
        """
        sections = []
        current_section = None
        
        for page in pages:
            lines = page.text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Identify section titles (uppercase, bold, etc.)
                if self._is_section_title(line):
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = PDFSection(
                        title=line,
                        start_page=page.page_number,
                        end_page=page.page_number,
                        content="",
                    )
                elif current_section and line:
                    current_section.content += line + "\n"
                    current_section.end_page = page.page_number
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    @staticmethod
    def _is_section_title(text: str) -> bool:
        """Checks if the text is a section title"""
        if not text:
            return False
        
        # Check if it's all uppercase
        if text.isupper() and len(text) > 3:
            return True
        
        # Check for common section titles
        common_titles = [
            "abstract", "introduction", "methodology", "method",
            "results", "discussion", "conclusion", "references",
            "acknowledgments", "appendix", "related work"
        ]
        
        text_lower = text.lower()
        return any(title in text_lower for title in common_titles)
    
    def extract_key_information(
        self,
        pdf_path: str,
        sections: Optional[List[PDFSection]] = None,
    ) -> ExtractedInfo:
        """
        Extracts key information from the paper
        
        Args:
            pdf_path: PDF file path
            sections: List of PDF sections (optional)
            
        Returns:
            ExtractedInfo: Extracted information
        """
        if sections is None:
            pages = self.extract_text(pdf_path)
            sections = self.parse_structure(pages)
        
        # If an LLM client is available, use it for intelligent parsing
        if self.llm_client and sections:
            return self._extract_with_llm(sections)
        else:
            return self._extract_local(sections)
    
    def _extract_with_llm(self, sections: List[PDFSection]) -> ExtractedInfo:
        """Smart extraction using LLM"""
        # Prepare prompt
        content_text = "\n\n".join([
            f"## {s.title}\n{s.content[:100]}"
            for s in sections  # Use only the first 5 sections
        ])
        
        prompt = f"""Extract key information from the following paper content, return in JSON format:

{content_text}

Please provide:
1. title: Paper title
2. authors: List of authors, split by ;
3. abstract: Abstract
4. methodology: Research methodology
5. results: Main results
6. key_contributions: Key contributions

### Output Requirements (must be strictly followed)
<response>
  <title> Paper title  </title> 
  <authors>List of authors</authors>
  <abstract>Abstract </abstract>
  <methodology> Research methodology </methodology>
  <results>Main results</results>
  <conclusion>  Key contributions </conclusion>
</response>
"""
        
        try:
            response = self.llm_client.call(prompt, max_tokens=10240 , temperature=0.3 ,output_format="json")
            info = self._parse_extraction_response(response)
            return info
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return self._extract_local(sections)
    
    def _extract_local(self, sections: List[PDFSection]) -> ExtractedInfo:
        """Local extraction (without LLM)"""
        return ExtractedInfo(
            title=self._find_section(sections, "title", ""),
            authors=[],
            abstract=self._find_section(sections, "abstract", ""),
            methodology=self._find_section(sections, "method", ""),
            results=self._find_section(sections, "results", ""),
            conclusion=self._find_section(sections, "conclusion", ""),
            figures=[],
            tables=[],
        )
    
    @staticmethod
    def _find_section(
        sections: List[PDFSection],
        keyword: str,
        default: str = ""
    ) -> str:
        """Finds a specific section"""
        for section in sections:
            if keyword.lower() in section.title.lower():
                return section.content[:1000]  # Return first 1000 characters
        return default
    
    @staticmethod
    def _parse_extraction_response(response: str) -> ExtractedInfo:
        """Parses LLM response"""
        title = None
        try:
            start_tag = "<title>"
            end_tag = "</title>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            title = response[start_idx:end_idx].strip()
        except ValueError:
            pass

        authors = []
        try:
            start_tag = "<authors>"
            end_tag = "</authors>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            concepts_text = response[start_idx:end_idx].strip()
            authors = [c.strip() for c in concepts_text.split(";") if c.strip()]
        except ValueError:
            pass
        abstract = None
        try:
            start_tag = "<abstract>"
            end_tag = "</abstract>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            abstract = response[start_idx:end_idx].strip()
        except ValueError:
            pass
        
        methodology = None
        try:
            start_tag = "<methodology>"
            end_tag = "</methodology>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            methodology = response[start_idx:end_idx].strip()
        except ValueError:
            pass
        
        results = None
        try:
            start_tag = "<results>"
            end_tag = "</results>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            results = response[start_idx:end_idx].strip()
        except ValueError:
            pass
        
        conclusion = None
        try:
            start_tag = "<conclusion>"
            end_tag = "</conclusion>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            conclusion = response[start_idx:end_idx].strip()
        except ValueError:
            pass
            
        return ExtractedInfo(
            title=title,
            authors=authors,
            abstract=abstract,
            methodology=methodology,
            results=results,
            conclusion=conclusion,
            figures=None,
            tables=None,
        )
        
    
    def extract_citations(self, pages: List[PDFPage]) -> List[str]:
        """
        Extracts citations
        
        Args:
            pages: List of PDF pages
            
        Returns:
            List[str]: List of citations
        """
        citations = []
        
        # Merge all text
        all_text = "\n".join([page.text for page in pages])
        
        # Find references section
        lines = all_text.split('\n')
        in_references = False
        
        for line in lines:
            line = line.strip()
            
            # Check if entering the references section
            if line.lower().startswith('references') or line.lower().startswith('bibliography'):
                in_references = True
                continue
            
            # Inside the references section
            if in_references and line:
                # Check if it looks like a citation (starts with number or author name)
                if self._looks_like_citation(line):
                    citations.append(line)
        
        return citations
    
    @staticmethod
    def _looks_like_citation(line: str) -> bool:
        """Checks if a line looks like a citation"""
        # Simple heuristic
        if not line:
            return False
        
        # Check if it starts with a number, bracket, or author name
        if line[0].isdigit():
            return True
        if line[0] in '([':
            return True
        if ',' in line and len(line) > 20:  # Has a comma and is long enough
            return True
        
        return False
