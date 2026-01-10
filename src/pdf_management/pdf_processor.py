"""
PDF 处理器 - 整合下载、缓存、解析的完整工作流
"""
from typing import Dict, Optional, List
from .downloader import PDFDownloader
from .parser import PDFParser, ExtractedInfo
from .cache_manager import CacheManager


class PDFProcessor:
    """PDF 处理器 - 完整的 PDF 管理工作流"""
    
    def __init__(
        self,
        cache_dir: str = "./cache/pdfs",
        llm_client=None,
        max_workers: int = 4,
    ):
        """
        初始化 PDF 处理器
        
        Args:
            cache_dir: 缓存目录
            llm_client: LLM 客户端
            max_workers: 最大并发下载数
        """
        self.downloader = PDFDownloader(cache_dir=cache_dir, max_workers=max_workers)
        self.parser = PDFParser(llm_client=llm_client)
        self.cache_manager = CacheManager(cache_dir=cache_dir)
        self.llm_client = llm_client
    
    def process_paper(
        self,
        paper: Dict,
        force_reprocess: bool = False,
    ) -> Dict:
        """
        处理单篇论文：下载 -> 解析 -> 提取
        
        Args:
            paper: 论文字典
                {
                    "paper_id": "...",
                    "url": "...",
                    "title": "...",
                    ...
                }
            force_reprocess: 是否强制重新处理（忽略缓存）
            
        Returns:
            Dict: 处理结果
                {
                    "success": bool,
                    "paper_id": str,
                    "pdf_path": str,
                    "extracted_info": ExtractedInfo,
                    "error": str,
                }
        """
        paper_id = paper.get("paper_id", "")
        url = paper.get("url", "")
        
        if not paper_id or not url:
            return {
                "success": False,
                "paper_id": paper_id,
                "pdf_path": None,
                "extracted_info": None,
                "error": "缺少 paper_id 或 url",
            }
        
        try:
            # 1. 检查缓存
            if not force_reprocess and self.cache_manager.has_cached_pdf(paper_id):
                cached_path = str(self.cache_manager.get_cache_path(paper_id))
                metadata = self.cache_manager.get_metadata(paper_id)
                
                # 如果已经提取过，直接返回
                if metadata and metadata.status == "extracted":
                    return {
                        "success": True,
                        "paper_id": paper_id,
                        "pdf_path": cached_path,
                        "extracted_info": metadata.metadata.get("extracted_info"),
                        "error": None,
                    }
            
            # 2. 下载 PDF
            print(f"📥 下载论文: {paper_id}")
            download_result = self.downloader.download_paper(url)
            
            if not download_result["success"]:
                return {
                    "success": False,
                    "paper_id": paper_id,
                    "pdf_path": None,
                    "extracted_info": None,
                    "error": f"下载失败: {download_result.get('error', '未知错误')}",
                }
            
            pdf_path = download_result["file_path"]
            
            # 3. 注册到缓存
            self.cache_manager.register_pdf(
                paper_id=paper_id,
                url=url,
                file_path=pdf_path,
                file_size=download_result["file_size"],
            )
            self.cache_manager.update_metadata(paper_id, status="processing")
            
            # 4. 解析 PDF
            print(f"📖 解析 PDF: {paper_id}")
            pages = self.parser.extract_text(pdf_path)
            
            if not pages:
                return {
                    "success": False,
                    "paper_id": paper_id,
                    "pdf_path": pdf_path,
                    "extracted_info": None,
                    "error": "无法提取 PDF 文本",
                }
            
            # 5. 提取关键信息
            print(f"🔍 提取信息: {paper_id}")
            sections = self.parser.parse_structure(pages)
            extracted_info = self.parser.extract_key_information(pdf_path, sections)
            
            # 6. 提取引用
            citations = self.parser.extract_citations(pages)
            
            # 7. 更新缓存元数据
            from datetime import datetime
            self.cache_manager.update_metadata(
                paper_id,
                status="extracted",
                metadata={
                    "extracted_info": self._convert_to_dict(extracted_info),
                    "citations": citations,
                    "page_count": len(pages),
                    "extracted_sections": len(sections),
                },
                extraction_date=datetime.now().isoformat(),
            )
            
            return {
                "success": True,
                "paper_id": paper_id,
                "pdf_path": pdf_path,
                "extracted_info": extracted_info,
                "citations": citations,
                "error": None,
            }
        
        except Exception as e:
            return {
                "success": False,
                "paper_id": paper_id,
                "pdf_path": None,
                "extracted_info": None,
                "error": f"处理失败: {str(e)}",
            }
    
    def process_papers_batch(
        self,
        papers: List[Dict],
        force_reprocess: bool = False,
    ) -> Dict:
        """
        批量处理论文
        
        Args:
            papers: 论文列表
            force_reprocess: 是否强制重新处理
            
        Returns:
            Dict: 处理结果统计
        """
        results = {
            "total": len(papers),
            "successful": 0,
            "failed": 0,
            "papers": {},
        }
        
        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}] 处理论文...")
            result = self.process_paper(paper, force_reprocess)
            
            paper_id = paper.get("paper_id", "")
            results["papers"][paper_id] = result
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    @staticmethod
    def _convert_to_dict(obj):
        """将对象转换为字典（用于 JSON 序列化）"""
        if isinstance(obj, dict):
            return obj
        
        # 如果是 dataclass
        if hasattr(obj, '__dataclass_fields__'):
            return {
                field: getattr(obj, field)
                for field in obj.__dataclass_fields__
            }
        
        return str(obj)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.cache_manager.get_cache_stats()
    
    def cleanup_cache(self, max_age_days: int = 30, max_size_mb: int = 5000):
        """清理缓存"""
        self.cache_manager.cleanup(max_age_days, max_size_mb)
