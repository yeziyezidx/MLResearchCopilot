"""
单元测试 - 意图理解模块
"""
import pytest
from src.core.intent_understanding import IntentUnderstanding, ResearchIntent


class TestIntentUnderstanding:
    
    def setup_method(self):
        """测试前准备"""
        self.understanding = IntentUnderstanding()
    
    def test_understand_basic(self):
        """测试基本意图理解"""
        query = "如何使用 Transformer 进行机器翻译?"
        intent = self.understanding.understand(query)
        
        assert isinstance(intent, ResearchIntent)
        assert intent.original_query == query
        assert intent.research_area is not None
        assert len(intent.research_questions) > 0
    
    def test_understand_with_context(self):
        """测试带背景信息的意图理解"""
        query = "如何改进模型效率?"
        context = "我们正在研究深度学习模型的优化"
        
        intent = self.understanding.understand(query, context)
        
        assert intent.context == context
        assert intent.original_query == query
    
    def test_intent_to_dict(self):
        """测试意图对象转字典"""
        query = "测试查询"
        intent = self.understanding.understand(query)
        
        intent_dict = intent.to_dict()
        
        assert isinstance(intent_dict, dict)
        assert "original_query" in intent_dict
        assert "research_questions" in intent_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
