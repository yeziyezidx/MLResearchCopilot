"""
PDF 管理模块 - 处理论文 PDF 的下载、存储、缓存和解析
"""

from .downloader import PDFDownloader, PDFDownloadError
from .parser import PDFParser, PDFPage, PDFSection, ExtractedInfo
from .cache_manager import CacheManager, CacheMetadata
from .pdf_processor import PDFProcessor

__all__ = [
    "PDFDownloader",
    "PDFDownloadError",
    "PDFParser",
    "PDFPage",
    "PDFSection",
    "ExtractedInfo",
    "CacheManager",
    "CacheMetadata",
    "PDFProcessor",
]
