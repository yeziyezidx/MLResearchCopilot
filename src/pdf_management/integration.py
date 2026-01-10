"""
PDF 集成适配器 - 将 PDF 处理集成到主流程
"""
from typing import List, Dict, Optional
from src.core.types import StructuredPaper
from src.pdf_management import PDFProcessor, ExtractedInfo


class PDFIntegrationAdapter:
    """PDF 集成适配器 - 连接 PDF 处理与主流程"""
    
    def __init__(self, llm_client=None, cache_dir: str = "./cache/pdfs"):
        """
        初始化集成适配器
        
        Args:
            llm_client: LLM 客户端
            cache_dir: PDF 缓存目录
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
        用 PDF 内容丰富论文信息
        
        Args:
            paper: 论文字典
            extract_pdf: 是否提取 PDF 内容
            
        Returns:
            Dict: 丰富后的论文信息
        """
        if not extract_pdf or not paper.get("url"):
            return paper
        
        try:
            # 处理 PDF
            result = self.processor.process_paper(paper)
            
            if result["success"]:
                extracted = result.get("extracted_info")
                
                # 用 PDF 内容更新论文信息
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
        批量丰富论文信息
        
        Args:
            papers: 论文列表
            extract_pdf: 是否提取 PDF 内容
            
        Returns:
            List[Dict]: 丰富后的论文列表
        """
        enriched = []
        
        for paper in papers:
            enriched_paper = self.enrich_paper_with_pdf(paper, extract_pdf)
            enriched.append(enriched_paper)
        
        return enriched
    
    @staticmethod
    def _extract_text_from_pdf(pdf_path: str) -> str:
        """从 PDF 提取全部文本"""
        try:
            import PyPDF2
            
            text = []
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            
            return "\n".join(text)
        
        except Exception as e:
            return f"[PDF 文本提取失败: {e}]"
    
    def generate_synthesis_from_pdf(
        self,
        paper: Dict,
        synthesis_prompt: Optional[str] = None,
    ) -> str:
        """
        从 PDF 内容生成综合总结
        
        Args:
            paper: 论文字典（已包含 pdf_content）
            synthesis_prompt: 综合提示词
            
        Returns:
            str: LLM 生成的总结
        """
        if not self.llm_client:
            return "LLM 客户端未配置"
        
        if not paper.get("pdf_content"):
            return "论文 PDF 内容未可用"
        
        pdf_content = paper["pdf_content"]
        
        # 准备内容
        content_text = f"""
论文标题: {paper.get('title', 'N/A')}

摘要:
{pdf_content.get('sections', {}).get('abstract', '')[:500]}

研究方法:
{pdf_content.get('sections', {}).get('methodology', '')[:500]}

主要结果:
{pdf_content.get('sections', {}).get('results', '')[:500]}

结论:
{pdf_content.get('sections', {}).get('conclusion', '')[:500]}
"""
        
        # 生成提示词
        if not synthesis_prompt:
            synthesis_prompt = """基于以下论文内容，请生成详细的研究总结，包括：
1. 研究的核心问题和创新点
2. 采用的主要方法和技术
3. 关键的研究成果和发现
4. 可能的应用和影响
5. 与相关工作的区别

请用中文回答，总结长度 200-300 字。"""
        
        prompt = f"""{synthesis_prompt}

论文内容:
{content_text}
"""
        
        try:
            response = self.llm_client.call(prompt)
            return response
        except Exception as e:
            return f"生成失败: {e}"
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.processor.get_cache_stats()
