"""
提示词管理模块
"""
from typing import Dict, List, Optional


class PromptManager:
    """提示词管理器"""
    
    # 系统提示词
    SYSTEM_PROMPTS = {
        "research_assistant": """你是一个专业的研究助手，帮助用户理解和分析学术论文。
你应该：
1. 提供准确、客观的分析
2. 引用具体的论文内容
3. 提出有建设性的批评和建议
4. 用清晰、学术的语言交流
5. 当不确定时要明确说明
""",
        
        "intent_analyzer": """你是一个研究意图分析专家。你的任务是理解用户的研究问题，
并将其转化为清晰、具体的研究目标和搜索查询。
请以结构化的方式回复。""",
        
        "paper_extractor": """你是一个论文信息抽取专家。你的任务是从论文的标题、摘要和内容中
提取关键信息，包括研究问题、方法、数据集、结果和贡献。
请返回结构化的 JSON 格式。""",
        
        "synthesis_expert": """你是一个文献综述专家。你的任务是综合多篇论文的信息，
识别共识、差异、研究缺口和未来方向。
请提供深入、有洞察力的分析。""",
    }
    
    # 任务提示词模板
    TASK_PROMPTS = {
        "extract_keywords": """从以下文本中提取关键词、技术术语和模型名称：

文本：{text}

请返回一个 JSON 对象，包含以下字段：
- keywords: 一般关键词列表
- technical_terms: 技术术语列表
- model_names: 模型名称列表
- paper_titles: 论文标题列表（如果有提及）
""",
        
        "understand_concept": """解释以下概念在机器学习和自然语言处理领域的含义：

概念：{concept}

请提供：
1. 定义
2. 主要特点
3. 应用场景
4. 相关概念
5. 推荐阅读的论文或资源
""",
        
        "formulate_problem": """基于以下信息，构建一个结构化的研究问题：

用户问题：{query}
关键词：{keywords}
研究领域：{domain}

请提供：
1. 清晰的问题陈述
2. 研究目标（3-5个）
3. 评估方法
4. 潜在的研究约束
5. 用于文献检索的优化查询（3-5个）
""",
        
        "extract_paper_info": """从以下论文信息中提取结构化数据：

标题：{title}
摘要：{abstract}

请返回 JSON 格式，包含：
- research_problem: 研究问题
- methods: 使用的方法列表
- datasets: 使用的数据集列表
- results: 主要结果
- contributions: 主要贡献
- limitations: 局限性
- keywords: 关键词
""",
        
        "synthesize_papers": """综合以下论文进行文献综述：

{papers_summary}

请提供：
1. 综合总结（300字左右）
2. 主要研究趋势
3. 主要的共识和争议
4. 研究缺口
5. 未来研究方向
""",
    }
    
    @classmethod
    def get_system_prompt(cls, task_type: str) -> str:
        """获取系统提示词"""
        return cls.SYSTEM_PROMPTS.get(task_type, cls.SYSTEM_PROMPTS["research_assistant"])
    
    @classmethod
    def get_task_prompt(cls, task_type: str, **kwargs) -> str:
        """获取任务提示词并填充参数"""
        template = cls.TASK_PROMPTS.get(task_type, "")
        if not template:
            return ""
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"提示词参数缺失: {e}")
            return template
    
    @classmethod
    def list_system_prompts(cls) -> List[str]:
        """列出所有系统提示词"""
        return list(cls.SYSTEM_PROMPTS.keys())
    
    @classmethod
    def list_task_prompts(cls) -> List[str]:
        """列出所有任务提示词"""
        return list(cls.TASK_PROMPTS.keys())
