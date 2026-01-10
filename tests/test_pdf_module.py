"""
PDF 模块测试
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import json
import os


# 测试缓存管理
class TestCacheManager:
    """缓存管理测试"""
    
    @pytest.fixture
    def cache_dir(self, tmp_path):
        """创建临时缓存目录"""
        return str(tmp_path / "cache")
    
    def test_register_pdf(self, cache_dir):
        """测试 PDF 注册"""
        from src.pdf_management import CacheManager
        
        cache = CacheManager(cache_dir=cache_dir)
        
        # 注册 PDF
        cache.register_pdf(
            paper_id="arxiv.2301.001",
            url="https://arxiv.org/pdf/2301.00001.pdf",
            file_path=f"{cache_dir}/2301.00001.pdf",
            file_size=1024000,
        )
        
        # 检查是否存在
        assert cache.has_cached_pdf("arxiv.2301.001")
    
    def test_cache_stats(self, cache_dir):
        """测试缓存统计"""
        from src.pdf_management import CacheManager
        
        cache = CacheManager(cache_dir=cache_dir)
        
        # 注册多个 PDF
        for i in range(3):
            cache.register_pdf(
                paper_id=f"paper_{i}",
                url=f"https://example.com/paper_{i}.pdf",
                file_path=f"{cache_dir}/paper_{i}.pdf",
                file_size=1024000,
            )
        
        stats = cache.get_cache_stats()
        
        assert stats["total_papers"] == 3
        assert stats["total_size_mb"] == pytest.approx(3.0, rel=0.1)
    
    def test_metadata_persistence(self, cache_dir):
        """测试元数据持久化"""
        from src.pdf_management import CacheManager
        
        cache1 = CacheManager(cache_dir=cache_dir)
        cache1.register_pdf(
            paper_id="test_paper",
            url="https://example.com/paper.pdf",
            file_path=f"{cache_dir}/paper.pdf",
            file_size=2048000,
        )
        
        # 创建新实例，应该能读取元数据
        cache2 = CacheManager(cache_dir=cache_dir)
        assert cache2.has_cached_pdf("test_paper")


# 测试 PDF 下载
class TestPDFDownloader:
    """PDF 下载测试"""
    
    def test_downloader_initialization(self, tmp_path):
        """测试下载器初始化"""
        from src.pdf_management import PDFDownloader
        
        downloader = PDFDownloader(cache_dir=str(tmp_path))
        assert downloader is not None
        assert downloader.cache_dir == str(tmp_path)
    
    def test_pdf_validation(self, tmp_path):
        """测试 PDF 验证"""
        from src.pdf_management import PDFDownloader
        
        # 创建有效的 PDF 文件
        pdf_path = tmp_path / "test.pdf"
        with open(pdf_path, 'wb') as f:
            # PDF 魔数
            f.write(b'%PDF-1.4\n')
            f.write(b'sample content')
        
        downloader = PDFDownloader(cache_dir=str(tmp_path))
        
        # 应该能验证 PDF
        result = downloader._validate_pdf(str(pdf_path))
        assert result is True


# 测试 PDF 解析
class TestPDFParser:
    """PDF 解析测试"""
    
    def test_parser_initialization(self):
        """测试解析器初始化"""
        from src.pdf_management import PDFParser
        
        parser = PDFParser()
        assert parser is not None
    
    def test_section_title_detection(self):
        """测试章节标题检测"""
        from src.pdf_management import PDFParser
        
        # 测试全大写标题
        assert PDFParser._is_section_title("ABSTRACT") is True
        assert PDFParser._is_section_title("INTRODUCTION") is True
        assert PDFParser._is_section_title("METHODOLOGY") is True
        
        # 测试小写标题
        assert PDFParser._is_section_title("abstract") is True
        assert PDFParser._is_section_title("Introduction") is True
        
        # 测试非标题
        assert PDFParser._is_section_title("This is a sentence") is False
    
    def test_citation_detection(self):
        """测试引用检测"""
        from src.pdf_management import PDFParser
        
        # 测试有效引用
        assert PDFParser._looks_like_citation("[1] Smith et al.") is True
        assert PDFParser._looks_like_citation("(2020) Author Name") is True
        
        # 测试无效引用
        assert PDFParser._looks_like_citation("This is text") is False
        assert PDFParser._looks_like_citation("") is False


# 测试 PDF 处理器
class TestPDFProcessor:
    """PDF 处理器测试"""
    
    def test_processor_initialization(self, tmp_path):
        """测试处理器初始化"""
        from src.pdf_management import PDFProcessor
        
        processor = PDFProcessor(cache_dir=str(tmp_path))
        assert processor is not None
        assert processor.cache_manager is not None
        assert processor.downloader is not None
    
    def test_dict_conversion(self):
        """测试对象转换"""
        from src.pdf_management import PDFProcessor, ExtractedInfo
        
        info = ExtractedInfo(
            title="Test Paper",
            authors=["Author 1"],
            abstract="Test abstract",
            introduction="Test intro",
            methodology="Test method",
            results="Test results",
            conclusion="Test conclusion",
            references=["Ref 1"],
            figures=[],
            tables=[],
        )
        
        converted = PDFProcessor._convert_to_dict(info)
        
        assert isinstance(converted, dict)
        assert converted["title"] == "Test Paper"
        assert converted["authors"] == ["Author 1"]


# 集成测试
class TestPDFIntegration:
    """PDF 集成测试"""
    
    def test_cache_and_download_integration(self, tmp_path):
        """测试缓存和下载集成"""
        from src.pdf_management import CacheManager, PDFDownloader
        
        cache_dir = str(tmp_path)
        cache = CacheManager(cache_dir=cache_dir)
        downloader = PDFDownloader(cache_dir=cache_dir)
        
        # 创建模拟下载
        paper_id = "test_paper"
        
        # 创建模拟 PDF 文件
        pdf_path = Path(cache_dir) / f"{paper_id}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        # 注册到缓存
        cache.register_pdf(
            paper_id=paper_id,
            url="https://example.com/paper.pdf",
            file_path=str(pdf_path),
            file_size=pdf_path.stat().st_size,
        )
        
        # 验证缓存
        assert cache.has_cached_pdf(paper_id)
        
        # 获取路径
        cached_path = cache.get_cache_path(paper_id)
        assert str(cached_path) == str(pdf_path)
    
    def test_paper_enrichment(self, tmp_path):
        """测试论文信息丰富"""
        from src.pdf_management.integration import PDFIntegrationAdapter
        
        adapter = PDFIntegrationAdapter(cache_dir=str(tmp_path))
        
        paper = {
            "paper_id": "test_001",
            "title": "Test Paper",
            "url": "https://example.com/paper.pdf",
        }
        
        # 注意：实际的 PDF 下载可能失败，这只是测试结构
        enriched = adapter.enrich_paper_with_pdf(paper, extract_pdf=False)
        
        # 确保论文结构保留
        assert enriched["paper_id"] == "test_001"
        assert enriched["title"] == "Test Paper"


# 性能测试
class TestPerformance:
    """性能测试"""
    
    def test_large_cache_metadata(self, tmp_path):
        """测试大型缓存元数据"""
        from src.pdf_management import CacheManager
        
        cache = CacheManager(cache_dir=str(tmp_path))
        
        # 注册 100 个 PDF
        for i in range(100):
            cache.register_pdf(
                paper_id=f"paper_{i:04d}",
                url=f"https://example.com/paper_{i}.pdf",
                file_path=f"{str(tmp_path)}/paper_{i}.pdf",
                file_size=1024000,
            )
        
        # 验证统计
        stats = cache.get_cache_stats()
        assert stats["total_papers"] == 100


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
