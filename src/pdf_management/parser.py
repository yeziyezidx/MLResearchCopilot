"""
PDF 解析器 - 支持文本提取、分段、元数据解析
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PDFPage:
    """PDF 页面"""
    page_number: int
    text: str
    metadata: Dict = None


@dataclass
class PDFSection:
    """PDF 部分"""
    title: str
    start_page: int
    end_page: int
    content: str
    subsections: List["PDFSection"] = None


@dataclass
class ExtractedInfo:
    """提取的信息"""
    title: str
    authors: List[str]
    abstract: str
    introduction: str
    methodology: str
    results: str
    conclusion: str
    references: List[str]
    figures: List[Dict]
    tables: List[Dict]


class PDFParser:
    """PDF 解析器"""
    
    def __init__(self, llm_client=None):
        """
        初始化 PDF 解析器
        
        Args:
            llm_client: LLM 客户端（用于智能解析）
        """
        self.llm_client = llm_client
    
    def extract_text(self, pdf_path: str) -> List[PDFPage]:
        """
        从 PDF 中提取文本
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            List[PDFPage]: PDF 页面列表
        """
        try:
            import PyPDF2
        except ImportError:
            print("警告: PyPDF2 未安装，使用基础解析")
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
            print(f"PDF 提取失败: {e}")
        
        return pages
    
    def _basic_text_extraction(self, pdf_path: str) -> List[PDFPage]:
        """基础文本提取（当 PyPDF2 不可用时）"""
        # 这是一个后备方案，实际应该使用 pdfplumber 或 PyPDF2
        return []
    
    def parse_structure(self, pages: List[PDFPage]) -> List[PDFSection]:
        """
        解析 PDF 结构（识别章节）
        
        Args:
            pages: PDF 页面列表
            
        Returns:
            List[PDFSection]: PDF 部分列表
        """
        sections = []
        current_section = None
        
        for page in pages:
            lines = page.text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 识别章节标题（大写、加粗等）
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
        """检查是否为章节标题"""
        if not text:
            return False
        
        # 检查是否全是大写
        if text.isupper() and len(text) > 3:
            return True
        
        # 检查常见的章节标题
        common_titles = [
            "abstract", "introduction", "methodology", "method",
            "results", "discussion", "conclusion", "references",
            "acknowledgments", "appendix"
        ]
        
        text_lower = text.lower()
        return any(title in text_lower for title in common_titles)
    
    def extract_key_information(
        self,
        pdf_path: str,
        sections: Optional[List[PDFSection]] = None,
    ) -> ExtractedInfo:
        """
        提取论文的关键信息
        
        Args:
            pdf_path: PDF 文件路径
            sections: PDF 部分列表（可选）
            
        Returns:
            ExtractedInfo: 提取的信息
        """
        if sections is None:
            pages = self.extract_text(pdf_path)
            sections = self.parse_structure(pages)
        
        # 如果有 LLM 客户端，使用 LLM 进行智能解析
        if self.llm_client and sections:
            return self._extract_with_llm(sections)
        else:
            return self._extract_local(sections)
    
    def _extract_with_llm(self, sections: List[PDFSection]) -> ExtractedInfo:
        """使用 LLM 进行智能提取"""
        # 准备提示词
        content_text = "\n\n".join([
            f"## {s.title}\n{s.content[:500]}"
            for s in sections[:5]  # 只使用前 5 个部分
        ])
        
        prompt = f"""从以下论文内容中提取关键信息，返回 JSON 格式:

{content_text}

请提供:
1. title: 论文标题
2. authors: 作者列表
3. abstract: 摘要
4. methodology: 研究方法
5. results: 主要结果
6. key_contributions: 主要贡献
"""
        
        try:
            response = self.llm_client.call(prompt)
            info = self._parse_extraction_response(response)
            return info
        except Exception as e:
            print(f"LLM 提取失败: {e}")
            return self._extract_local(sections)
    
    def _extract_local(self, sections: List[PDFSection]) -> ExtractedInfo:
        """本地提取（不使用 LLM）"""
        return ExtractedInfo(
            title=self._find_section(sections, "title", ""),
            authors=[],
            abstract=self._find_section(sections, "abstract", ""),
            introduction=self._find_section(sections, "introduction", ""),
            methodology=self._find_section(sections, "method", ""),
            results=self._find_section(sections, "results", ""),
            conclusion=self._find_section(sections, "conclusion", ""),
            references=[],
            figures=[],
            tables=[],
        )
    
    @staticmethod
    def _find_section(
        sections: List[PDFSection],
        keyword: str,
        default: str = ""
    ) -> str:
        """查找特定章节"""
        for section in sections:
            if keyword.lower() in section.title.lower():
                return section.content[:1000]  # 返回前 1000 字符
        return default
    
    @staticmethod
    def _parse_extraction_response(response: str) -> ExtractedInfo:
        """解析 LLM 响应"""
        import json
        
        try:
            # 尝试解析 JSON
            data = json.loads(response)
            
            return ExtractedInfo(
                title=data.get("title", ""),
                authors=data.get("authors", []),
                abstract=data.get("abstract", ""),
                introduction=data.get("introduction", ""),
                methodology=data.get("methodology", ""),
                results=data.get("results", ""),
                conclusion=data.get("conclusion", ""),
                references=data.get("references", []),
                figures=data.get("figures", []),
                tables=data.get("tables", []),
            )
        except json.JSONDecodeError:
            # 如果不是 JSON，返回默认值
            return ExtractedInfo(
                title="", authors=[], abstract="",
                introduction="", methodology="", results="",
                conclusion="", references=[], figures=[], tables=[]
            )
    
    def extract_citations(self, pages: List[PDFPage]) -> List[str]:
        """
        提取引用
        
        Args:
            pages: PDF 页面列表
            
        Returns:
            List[str]: 引用列表
        """
        citations = []
        
        # 合并所有文本
        all_text = "\n".join([page.text for page in pages])
        
        # 查找引用部分
        lines = all_text.split('\n')
        in_references = False
        
        for line in lines:
            line = line.strip()
            
            # 检查是否进入引用部分
            if line.lower().startswith('references') or line.lower().startswith('bibliography'):
                in_references = True
                continue
            
            # 在引用部分中
            if in_references and line:
                # 检查是否看起来像引用（以数字或作者名开头）
                if self._looks_like_citation(line):
                    citations.append(line)
        
        return citations
    
    @staticmethod
    def _looks_like_citation(line: str) -> bool:
        """检查是否看起来像引用"""
        # 简单的启发式方法
        if not line:
            return False
        
        # 检查是否以数字、括号或作者名开头
        if line[0].isdigit():
            return True
        if line[0] in '([':
            return True
        if ',' in line and len(line) > 20:  # 有逗号且足够长
            return True
        
        return False
