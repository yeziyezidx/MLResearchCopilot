"""
单元测试 - 综合分析模块
"""
import pytest
from src.synthesis.aggregator import Aggregator
from src.synthesis.summarizer import Summarizer
from src.extraction.structured_output import StructuredPaper


class TestAggregator:
    
    def setup_method(self):
        """测试前准备"""
        self.aggregator = Aggregator()
        self.sample_papers = [
            self._create_sample_paper(1),
            self._create_sample_paper(2),
            self._create_sample_paper(3),
        ]
    
    @staticmethod
    def _create_sample_paper(idx):
        return StructuredPaper(
            paper_id=f"paper_{idx}",
            title=f"Test Paper {idx}",
            authors=[f"Author {idx}"],
            abstract=f"Abstract for paper {idx}",
            url=f"https://example.com/paper{idx}.pdf",
            source="test_source",
            research_problem=f"Problem {idx}",
            keywords=[f"keyword{idx}", "common_keyword"],
            citations_count=idx * 10,
        )
    
    def test_aggregate_keywords(self):
        """测试关键词聚合"""
        result = self.aggregator.aggregate_keywords(self.sample_papers)
        
        assert isinstance(result, dict)
        assert "common_keyword" in result
        assert result["common_keyword"] == 3


class TestSummarizer:
    
    def setup_method(self):
        """测试前准备"""
        self.summarizer = Summarizer()
        self.sample_papers = [
            StructuredPaper(
                paper_id=f"paper_{i}",
                title=f"Test Paper {i}",
                authors=[f"Author {i}"],
                abstract=f"Abstract for paper {i}",
                url=f"https://example.com/paper{i}.pdf",
                source="test_source",
            )
            for i in range(3)
        ]
    
    def test_synthesize(self):
        """测试综合总结"""
        result = self.summarizer.synthesize(self.sample_papers)
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "insights" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
