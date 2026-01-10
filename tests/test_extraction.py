"""
单元测试 - 信息抽取模块
"""
import pytest
from src.extraction.paper_extractor import PaperExtractor
from src.extraction.structured_output import StructuredPaper


class TestPaperExtractor:
    
    def setup_method(self):
        """测试前准备"""
        self.extractor = PaperExtractor()
        self.sample_paper = {
            "paper_id": "2023.test.001",
            "title": "Testing Deep Learning Models",
            "authors": ["Author One", "Author Two"],
            "abstract": "This paper presents a novel approach to testing deep learning models...",
            "url": "https://example.com/paper.pdf",
            "source": "arxiv",
            "published_date": "2023-01-01",
        }
    
    def test_extract_basic(self):
        """测试基本信息抽取"""
        result = self.extractor.extract(self.sample_paper)
        
        assert isinstance(result, StructuredPaper)
        assert result.paper_id == self.sample_paper["paper_id"]
        assert result.title == self.sample_paper["title"]
        assert len(result.authors) == 2
    
    def test_extract_to_dict(self):
        """测试提取结果转字典"""
        result = self.extractor.extract(self.sample_paper)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["title"] == self.sample_paper["title"]
    
    def test_extract_to_table_row(self):
        """测试提取结果转表格行"""
        result = self.extractor.extract(self.sample_paper)
        row = result.to_table_row()
        
        assert "Title" in row
        assert "Authors" in row
        assert "Source" in row


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
