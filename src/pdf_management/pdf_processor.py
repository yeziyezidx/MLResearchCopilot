"""
PDF processor - including download, cache, parse
"""
from typing import Dict, Optional, List
from .downloader import PDFDownloader
from .parser import PDFParser, ExtractedInfo
from .cache_manager import CacheManager
import hashlib

class PDFProcessor:
    """PDF procesor """
    
    def __init__(
        self,
        cache_dir: str = "./cache/pdfs",
        llm_client=None,
        max_workers: int = 4,
    ):
        """
        initialize PDF prcessor
        
        Args:
            cache_dir: cache dir
            llm_client: LLM clicent
            max_workers: number of workers that download pdf
        """
        self.downloader = PDFDownloader(download_dir=cache_dir, max_workers=max_workers)
        self.parser = PDFParser(llm_client=llm_client)
        self.cache_manager = CacheManager(cache_dir=cache_dir)
        self.llm_client = llm_client
    
    def process_paper(
        self,
        paper: Dict,
        urlkey: str = "pdf_url",
        force_reprocess: bool = False,
    ) -> Dict:
        """
        process single paper: download -> parse -> extraction
        
        Args:
            paper: paper dict
                {
                    "paper_id": "...",
                    "url": "...",
                    "title": "...",
                    ...
                }
            force_reprocess: if repprocess in force
            
        Returns:
            Dict: process result
                {
                    "success": bool,
                    "paper_id": str,
                    "pdf_path": str,
                    "extracted_info": ExtractedInfo,
                    "error": str,
                }
        """
        url = paper.get(urlkey, "")
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        paper_id = url_hash
        
        if not paper_id or not url:
            return {
                "success": False,
                "paper_id": paper_id,
                "url": url,
                "pdf_path": None,
                "extracted_info": None,
                "error": "missing paper_id or url",
            }
        
        try:
            # 1. check cache
            if not force_reprocess and self.cache_manager.has_cached_pdf(paper_id):
                cached_path = str(self.cache_manager.get_cache_path(paper_id))
                metadata = self.cache_manager.get_metadata(paper_id)
                
                # if already has metadata, return
                if metadata and metadata.status == "extracted":
                    return {
                        "success": True,
                        "paper_id": paper_id,
                        "url": url,
                        "pdf_path": cached_path,
                        "extracted_info": metadata.metadata.get("extracted_info"),
                        "error": None,
                    }
            
            # 2. download PDF
            print(f"📥 download paper: {paper_id} url: {url}")
            download_result = self.downloader.download_paper(url)
            
            if not download_result["success"]:
                return {
                    "success": False,
                    "paper_id": paper_id,
                    "url": url,
                    "pdf_path": None,
                    "extracted_info": None,
                    "error": f"download failed: {download_result.get('error', 'unknow issue')}",
                }
            
            pdf_path = download_result["file_path"]
            
            # 3. register cache
            self.cache_manager.register_pdf(
                paper_id=paper_id,
                url=url,
                file_path=pdf_path,
                file_size=download_result["file_size"],
            )
            self.cache_manager.update_metadata(paper_id, status="processing")
            
            # 4. parse PDF
            print(f"📖 parse PDF: {paper_id}, url: {url}")
            pages = self.parser.extract_text(pdf_path)
            
            if not pages:
                return {
                    "success": False,
                    "paper_id": paper_id,
                    "url": url,
                    "pdf_path": pdf_path,
                    "extracted_info": None,
                    "error": "can't parse PDF text",
                }
            
            # 5. extract info
            print(f"🔍 extract info: {paper_id}")
            sections = self.parser.parse_structure(pages)
            extracted_info = self.parser.extract_key_information(pdf_path, sections)
            print(extracted_info.title )
            print(extracted_info.contributions)
            
            # 6. extract citations
            citations = self.parser.extract_citations(pages)
            
            # 7. update metatda cache
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
                "url": url,
                "pdf_path": pdf_path,
                "extracted_info": extracted_info,
                "citations": citations,
                "error": None,
            }
        
        except Exception as e:
            return {
                "success": False,
                "paper_id": paper_id,
                "url": url,
                "pdf_path": None,
                "extracted_info": None,
                "error": f"process failed: {str(e)}",
            }
    
    def process_papers_batch(
        self,
        papers: List[Dict],
        urlkey: str = "pdf_url",
        force_reprocess: bool = False,
    ) -> Dict:
        """
        process papers by batch
        
        Args:
            papers: paper list
            force_reprocess: if reprocess in force
            
        Returns:
            Dict: process result stats
        """
        results = {
            "total": len(papers),
            "successful": 0,
            "failed": 0,
            "papers": {},
        }
        
        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}] processing paper...")
            result = self.process_paper(paper, urlkey, force_reprocess)
            
            paper_id = result["paper_id"]
            results["papers"][paper_id] = result
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    @staticmethod
    def _convert_to_dict(obj):
        """convert to dict (used for JSON serialize"""
        if isinstance(obj, dict):
            return obj
        
        # if it is dataclass
        if hasattr(obj, '__dataclass_fields__'):
            return {
                field: getattr(obj, field)
                for field in obj.__dataclass_fields__
            }
        
        return str(obj)
    
    def get_cache_stats(self) -> Dict:
        """get cache stats"""
        return self.cache_manager.get_cache_stats()
    
    def cleanup_cache(self, max_age_days: int = 30, max_size_mb: int = 5000):
        """cleanup cache"""
        self.cache_manager.cleanup(max_age_days, max_size_mb)
