"""
PDF 缓存管理器 - 管理本地 PDF 存储、版本控制和清理策略
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path


class CacheMetadata:
    """缓存元数据"""
    
    def __init__(self, paper_id: str, url: str, file_path: str):
        self.paper_id = paper_id
        self.url = url
        self.file_path = file_path
        self.downloaded_date = datetime.now().isoformat()
        self.file_size = 0  # 字节
        self.file_hash = ""
        self.version = 1
        self.status = "cached"  # cached, processing, extracted
        self.extraction_date = None
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "paper_id": self.paper_id,
            "url": self.url,
            "file_path": self.file_path,
            "downloaded_date": self.downloaded_date,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "version": self.version,
            "status": self.status,
            "extraction_date": self.extraction_date,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CacheMetadata":
        """从字典创建"""
        obj = cls(
            paper_id=data.get("paper_id", ""),
            url=data.get("url", ""),
            file_path=data.get("file_path", ""),
        )
        obj.file_size = data.get("file_size", 0)
        obj.file_hash = data.get("file_hash", "")
        obj.version = data.get("version", 1)
        obj.status = data.get("status", "cached")
        obj.extraction_date = data.get("extraction_date")
        obj.metadata = data.get("metadata", {})
        return obj


class CacheManager:
    """PDF 缓存管理器"""
    
    def __init__(self, cache_dir: str = "./cache/pdfs"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata_cache: Dict[str, CacheMetadata] = {}
        
        # 加载现有元数据
        self._load_metadata()
    
    def _load_metadata(self):
        """从磁盘加载元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for paper_id, meta_data in data.items():
                        self.metadata_cache[paper_id] = CacheMetadata.from_dict(meta_data)
            except Exception as e:
                print(f"加载元数据失败: {e}")
    
    def _save_metadata(self):
        """保存元数据到磁盘"""
        try:
            data = {
                paper_id: meta.to_dict()
                for paper_id, meta in self.metadata_cache.items()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存元数据失败: {e}")
    
    def get_cache_path(self, paper_id: str) -> Path:
        """获取论文的缓存路径"""
        return self.cache_dir / f"{paper_id}.pdf"
    
    def has_cached_pdf(self, paper_id: str) -> bool:
        """检查是否已缓存该论文"""
        if paper_id in self.metadata_cache:
            file_path = self.get_cache_path(paper_id)
            return file_path.exists()
        return False
    
    def register_pdf(
        self,
        paper_id: str,
        url: str,
        file_path: str,
        file_size: int = 0,
    ) -> CacheMetadata:
        """
        注册一个新的 PDF 文件到缓存
        
        Args:
            paper_id: 论文 ID
            url: 论文 URL
            file_path: 本地文件路径
            file_size: 文件大小
            
        Returns:
            CacheMetadata: 缓存元数据
        """
        metadata = CacheMetadata(paper_id, url, file_path)
        metadata.file_size = file_size
        
        # 计算文件哈希
        if os.path.exists(file_path):
            metadata.file_hash = self._calculate_file_hash(file_path)
        
        self.metadata_cache[paper_id] = metadata
        self._save_metadata()
        
        return metadata
    
    def get_metadata(self, paper_id: str) -> Optional[CacheMetadata]:
        """获取论文的缓存元数据"""
        return self.metadata_cache.get(paper_id)
    
    def update_metadata(
        self,
        paper_id: str,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None,
        extraction_date: Optional[str] = None,
    ):
        """更新缓存元数据"""
        if paper_id in self.metadata_cache:
            meta = self.metadata_cache[paper_id]
            
            if status:
                meta.status = status
            if metadata:
                meta.metadata.update(metadata)
            if extraction_date:
                meta.extraction_date = extraction_date
            
            self._save_metadata()
    
    def get_all_cached_papers(self) -> List[str]:
        """获取所有已缓存的论文 ID"""
        return list(self.metadata_cache.keys())
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_size = 0
        cached_count = 0
        extracted_count = 0
        
        for paper_id, meta in self.metadata_cache.items():
            file_path = self.get_cache_path(paper_id)
            if file_path.exists():
                cached_count += 1
                total_size += file_path.stat().st_size
                if meta.status == "extracted":
                    extracted_count += 1
        
        return {
            "total_papers": len(self.metadata_cache),
            "cached_papers": cached_count,
            "extracted_papers": extracted_count,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_directory": str(self.cache_dir),
        }
    
    def cleanup(self, max_age_days: int = 30, max_size_mb: int = 5000):
        """
        清理缓存
        
        Args:
            max_age_days: 最大天数（超过此时间的论文将被删除）
            max_size_mb: 最大缓存大小（MB）
        """
        from datetime import timedelta
        
        now = datetime.now()
        papers_to_delete = []
        
        # 检查日期
        for paper_id, meta in self.metadata_cache.items():
            downloaded_date = datetime.fromisoformat(meta.downloaded_date)
            age = now - downloaded_date
            
            if age > timedelta(days=max_age_days):
                papers_to_delete.append(paper_id)
        
        # 检查总大小
        stats = self.get_cache_stats()
        if stats["total_size_mb"] > max_size_mb and papers_to_delete:
            # 删除最旧的论文
            papers_to_delete.sort(
                key=lambda p: self.metadata_cache[p].downloaded_date
            )
        
        # 执行删除
        for paper_id in papers_to_delete:
            self.delete_cached_pdf(paper_id)
    
    def delete_cached_pdf(self, paper_id: str):
        """删除缓存的 PDF"""
        file_path = self.get_cache_path(paper_id)
        
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"删除文件失败: {e}")
        
        if paper_id in self.metadata_cache:
            del self.metadata_cache[paper_id]
            self._save_metadata()
    
    @staticmethod
    def _calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
        """计算文件哈希值"""
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
