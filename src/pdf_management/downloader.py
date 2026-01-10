"""
PDF 下载器 - 支持并发下载、重试、超时控制和进度跟踪
"""
import os
import requests
from typing import Optional, Callable, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class PDFDownloadError(Exception):
    """PDF 下载错误"""
    pass


class PDFDownloader:
    """PDF 下载器"""
    
    # 通用的 HTTP 请求头
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
        初始化 PDF 下载器
        
        Args:
            download_dir: 下载目录
            max_workers: 最大并发下载数
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            chunk_size: 每次读取的字节数
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
        下载单篇论文 PDF
        
        Args:
            url: 论文 URL
            output_path: 输出路径（默认从 URL 生成）
            progress_callback: 进度回调函数
            
        Returns:
            Dict: 下载结果
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
        
        # 如果文件已存在，跳过下载
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
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"下载失败，{wait_time} 秒后重试: {str(e)}")
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
        """执行单次下载尝试"""
        try:
            response = requests.get(
                url,
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
            
            # 检查是否真的是 PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and response.content[:4] != b'%PDF':
                raise PDFDownloadError(f"无效的 PDF 内容类型: {content_type}")
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 下载文件
            downloaded_size = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 调用进度回调
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
            raise PDFDownloadError(f"请求失败: {str(e)}")
        except IOError as e:
            raise PDFDownloadError(f"文件写入失败: {str(e)}")
    
    def download_papers_batch(
        self,
        papers: list,
        progress_callback: Optional[Callable] = None,
    ) -> Dict:
        """
        批量下载论文 PDF
        
        Args:
            papers: 论文列表
                [
                    {"paper_id": "...", "url": "..."},
                    ...
                ]
            progress_callback: 进度回调函数
            
        Returns:
            Dict: 下载结果统计
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
                        "error": "URL 缺失",
                    }
                    continue
                
                output_path = self._generate_output_path(url, paper_id)
                
                future = executor.submit(
                    self.download_paper,
                    url,
                    output_path,
                    progress_callback,
                )
                futures[future] = paper_id
            
            # 收集结果
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
    
    def _generate_output_path(self, url: str, paper_id: Optional[str] = None) -> str:
        """生成输出路径"""
        import hashlib
        
        if paper_id:
            filename = f"{paper_id}.pdf"
        else:
            # 从 URL 生成哈希作为文件名
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"paper_{url_hash}.pdf"
        
        return str(self.download_dir / filename)
    
    def get_download_stats(self) -> Dict:
        """获取下载统计信息"""
        return {
            **self.download_stats,
            "success_rate": (
                self.download_stats["successful"] / self.download_stats["total"]
                if self.download_stats["total"] > 0
                else 0
            ),
            "total_size_mb": self.download_stats["total_bytes"] / (1024 * 1024),
        }
