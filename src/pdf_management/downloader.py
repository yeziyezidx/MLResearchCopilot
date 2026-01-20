"""
PDF downloader - support download by parallel, retry and timeout
"""
import os
import requests
from typing import Optional, Callable, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class PDFDownloadError(Exception):
    """PDF download error"""
    pass


class PDFDownloader:
    """PDF downloader"""
    
    # HTTP header
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                     '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/pdf,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    def __init__(
        self,
        download_dir: str = "./cache/pdfs",
        max_workers: int = 4,
        timeout: int = 30,
        max_retries: int = 3,
        chunk_size: int = 8192,
    ):
        """
        initailize PDF downloader
        
        Args:
            download_dir: downloader dir
            max_workers: max workers
            timeout: timeout by seconds
            max_retries: max retries
            chunk_size: chunk size by bytes
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        
        self.download_stats = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "total_bytes": 0,
        }
    
    def download_paper(
        self,
        url: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict:
        """
        download PDF
        
        Args:
            url: paper URL
            output_path: output dir (by url)
            progress_callback: progress callback
            
        Returns:
            Dict: download result
                {
                    "success": bool,
                    "url": str,
                    "file_path": str or None,
                    "file_size": int,
                    "error": str or None,
                }
        """
        if output_path is None:
            output_path = self._generate_output_path(url)
        
        result = {
            "success": False,
            "url": url,
            "file_path": None,
            "file_size": 0,
            "error": None,
        }
        
        # if file exists, skip
        if os.path.exists(output_path):
            result["success"] = True
            result["file_path"] = output_path
            result["file_size"] = os.path.getsize(output_path)
            return result
        
        for attempt in range(self.max_retries):
            try:
                result = self._download_with_retry(url, output_path, progress_callback)
                
                if result["success"]:
                    self.download_stats["successful"] += 1
                    self.download_stats["total_bytes"] += result["file_size"]
                    return result
                    
            except PDFDownloadError as e:
                result["error"] = str(e)
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  
                    print(f"download failed, {wait_time} seconds later retry: {str(e)}")
                    time.sleep(wait_time)
        
        self.download_stats["failed"] += 1
        result["success"] = False
        return result
    
    def _download_with_retry(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict:
        """download with retry"""
        try:
            response = requests.get(
                url,
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
            
            # check if it's valid PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and response.content[:4] != b'%PDF':
                raise PDFDownloadError(f"invalid PDF content type: {content_type}")
            
            # get total file size
            total_size = int(response.headers.get('content-length', 0))
            
            # download file
            downloaded_size = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # call progress callback
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded_size, total_size)
            
            return {
                "success": True,
                "url": url,
                "file_path": output_path,
                "file_size": os.path.getsize(output_path),
                "error": None,
            }
            
        except requests.RequestException as e:
            raise PDFDownloadError(f"request failed: {str(e)}")
        except IOError as e:
            raise PDFDownloadError(f"file writer failed: {str(e)}")
    
    def download_papers_batch(
        self,
        papers: list,
        progress_callback: Optional[Callable] = None,
    ) -> Dict:
        """
        download PDF by batch
        
        Args:
            papers: paper list
                [
                    {"paper_id": "...", "url": "..."},
                    ...
                ]
            progress_callback: progress callback
            
        Returns:
            Dict: download result stats
        """
        results = {}
        self.download_stats["total"] = len(papers)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for paper in papers:
                paper_id = paper.get("paper_id", "")
                url = paper.get("url", "")
                
                if not url:
                    results[paper_id] = {
                        "success": False,
                        "error": "URL missing",
                    }
                    continue
                
                output_path = self._generate_output_path(url)
                
                future = executor.submit(
                    self.download_paper,
                    url,
                    output_path,
                    progress_callback,
                )
                futures[future] = paper_id
            
            # collect result
            for future in as_completed(futures):
                paper_id = futures[future]
                try:
                    result = future.result()
                    results[paper_id] = result
                except Exception as e:
                    results[paper_id] = {
                        "success": False,
                        "error": str(e),
                    }
        
        return {
            "total": self.download_stats["total"],
            "successful": self.download_stats["successful"],
            "failed": self.download_stats["failed"],
            "total_bytes": self.download_stats["total_bytes"],
            "results": results,
        }
    
    def _generate_output_path(self, url: str) -> str:
        """generate output path"""
        import hashlib
        # generate hashlib as file name from URL name
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"paper_{url_hash}.pdf"
        
        return str(self.download_dir / filename)
    
    def get_download_stats(self) -> Dict:
        """get download stats"""
        return {
            **self.download_stats,
            "success_rate": (
                self.download_stats["successful"] / self.download_stats["total"]
                if self.download_stats["total"] > 0
                else 0
            ),
            "total_size_mb": self.download_stats["total_bytes"] / (1024 * 1024),
        }
