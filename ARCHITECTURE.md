# ML Research Copilot - 架构文档

## 项目概述

ML Research Copilot 是一个智能研究辅助系统，帮助用户理解和分析学术论文。它使用自然语言处理和 LLM 技术，自动化文献综述的各个环节。

## 核心流程

```
用户问题
   ↓
意图理解 [by LLM]
   ↓
关键词提取 [by LLM]
   ↓
概念理解 [by Web Search]
   ↓
问题构建 [by LLM]
   ↓
多源检索 [Semantic Scholar, arXiv, GitHub]
   ↓
候选论文 (Top-K)
   ↓
结构化信息抽取 [by LLM]
   ↓
跨论文聚合 [by Aggregator]
   ↓
多文档综合 [by LLM]
   ↓
引用溯源 [by Citation Tracker]
   ↓
用户交互编辑
```

## 模块架构

### 1. 核心理解模块 (`src/core/`)

#### IntentUnderstanding (intent_understanding.py)
- **功能**: 理解用户的研究意图
- **输入**: 用户问题、背景信息
- **输出**: `ResearchIntent` 对象
  - intent_type: 研究意图类型
  - research_area: 研究领域
  - key_topics: 关键主题
  - research_questions: 细化的研究问题

#### KeywordExtractor (keyword_extraction.py)
- **功能**: 从问题中抽取关键词和专业术语
- **输入**: 文本或查询
- **输出**: `KeywordSet` 对象
  - general_keywords: 通用关键词
  - technical_terms: 技术术语
  - model_names: 模型名称
  - paper_names: 论文名称
  - method_terms: 方法术语

#### ConceptUnderstanding (concept_understanding.py)
- **功能**: 理解和定义关键概念
- **输入**: 关键词列表
- **输出**: `ConceptDefinition` 字典
  - concept: 概念名称
  - definition: 定义
  - examples: 示例
  - related_concepts: 相关概念

#### ProblemFormulator (problem_formulation.py)
- **功能**: 将用户问题转化为结构化的域问题
- **输入**: 查询、关键词、意图
- **输出**: `DomainProblem` 对象
  - problem_statement: 问题陈述
  - research_objectives: 研究目标
  - evaluation_metrics: 评估指标
  - search_queries: 搜索查询

### 2. 检索模块 (`src/retrieval/`)

#### SemanticSearcher (semantic_search.py)
- **功能**: 基于语义相似度的论文检索
- **方法**: 向量化 + 余弦相似度
- **输出**: `SearchResult` 列表

#### PaperSourceManager (paper_sources.py)
- **功能**: 管理多个论文来源
- **支持的源**:
  - ArxivSource: arXiv 论文库
  - SemanticScholarSource: Semantic Scholar
  - HuggingFaceSource: Hugging Face 模型库
- **可扩展**: 支持注册自定义论文源

#### Retriever (retriever.py)
- **功能**: 综合检索器，整合多个检索方法
- **方法**: 
  - search(): 基于查询列表检索
  - search_by_keywords(): 基于关键词检索

### 3. 信息抽取模块 (`src/extraction/`)

#### PaperMetadata (metadata.py)
- **功能**: 定义论文的结构化元数据
- **字段分类**:
  - REQUIRED_FIELDS: paper_id, title, authors, abstract
  - OPTIONAL_FIELDS: publication_date, venue, url, doi 等
  - EXTRACTION_FIELDS: research_problem, methods, datasets, results 等

#### StructuredPaper (structured_output.py)
- **功能**: 论文的完整结构化表示
- **主要字段**:
  - 基本信息: paper_id, title, authors, abstract, url, source
  - 内容抽取: research_problem, methods, datasets, results
  - 分析字段: contributions, limitations, future_work
  - 元数据: tags, keywords, citations_count, venue, doi

#### PaperExtractor (paper_extractor.py)
- **功能**: 从论文中抽取结构化信息
- **方法**:
  - extract(): 抽取论文信息
  - _extract_with_llm(): 使用 LLM 进行深度抽取
  - _populate_extracted_info(): 填充抽取结果

### 4. 综合分析模块 (`src/synthesis/`)

#### Aggregator (aggregator.py)
- **功能**: 跨论文信息聚合
- **方法**:
  - aggregate_methods(): 聚合使用的方法
  - aggregate_datasets(): 聚合使用的数据集
  - aggregate_metrics(): 聚合评估指标
  - aggregate_keywords(): 聚合关键词
  - generate_summary(): 生成汇总统计

#### CitationTracker (citation_tracking.py)
- **功能**: 进行句子级别的引用溯源
- **方法**:
  - track_citations(): 追踪句子中的引用
  - extract_evidence_sentences(): 提取证据句子及上下文

#### Summarizer (summarizer.py)
- **功能**: 多文档综合总结
- **方法**:
  - synthesize(): 综合多篇论文
  - _extract_insights(): 提取洞察
  - _identify_consensus(): 识别共识
  - _identify_gaps(): 识别研究缺口
  - _suggest_future_directions(): 建议未来方向

### 5. LLM 集成模块 (`src/llm/`)

#### LLMClient (client.py)
- **功能**: 与 LLM API 交互
- **支持**:
  - OpenAI API (GPT-4, GPT-3.5 等)
  - 本地模型 (通过兼容 API)
- **方法**:
  - call(): 基本 LLM 调用
  - call_with_function(): 函数调用

#### PromptManager (prompts.py)
- **功能**: 管理和模板化提示词
- **包含**:
  - 系统提示词 (research_assistant, intent_analyzer 等)
  - 任务提示词 (extract_keywords, extract_paper_info 等)

#### 工具函数 (utils.py)
- extract_json(): 从文本中提取 JSON
- format_list(): 格式化列表
- extract_keywords(): 关键词抽取
- clean_text(): 文本清理
- truncate_text(): 文本截断

### 6. Web UI 模块 (`src/ui/`)

#### WebApp (web_app.py)
- **框架**: Flask
- **路由**:
  - `/`: 首页
  - `/results`: 结果页面
  - `/health`: 健康检查

#### API (api.py)
- **端点**:
  - `POST /api/query`: 提交查询
  - `GET /api/results/<query_id>`: 获取结果
  - `GET/POST /api/papers`: 论文管理
  - `PUT /api/papers/<paper_id>`: 更新论文
  - `DELETE /api/papers/<paper_id>`: 删除论文
  - `GET /api/summary/<query_id>`: 获取综合总结

#### 前端模板
- `index.html`: 查询输入页面
- `results.html`: 结果展示页面

## 工作流示例

```python
from src.main import ResearchEngine

# 初始化引擎
engine = ResearchEngine()

# 处理查询
query_id = engine.process_query(
    query="Transformer 在机器翻译中的应用",
    context="我们需要了解 Attention 机制的发展"
)

# 获取结果
results = engine.get_results(query_id)
papers = results.get('papers', [])
synthesis = results.get('synthesis', {})
```

## 配置管理

### 配置类 (`src/config.py`)

- **Config**: 基础配置
  - OPENAI_API_KEY: OpenAI API 密钥
  - OPENAI_MODEL: 使用的模型 (默认: gpt-4)
  - SEMANTIC_SCHOLAR_API_KEY: Semantic Scholar API 密钥
  - SEARCH_TOP_K: 默认检索数量 (默认: 10)
  - DATABASE_URL: 数据库 URL
  - HOST, PORT: Web 应用配置

- **DevelopmentConfig**: 开发配置 (DEBUG=True)
- **ProductionConfig**: 生产配置 (DEBUG=False)
- **TestingConfig**: 测试配置 (内存数据库)

### 环境变量配置

创建 `.env` 文件（参考 `.env.example`）：

```
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4
SEMANTIC_SCHOLAR_API_KEY=your_key
HOST=0.0.0.0
PORT=5000
DEBUG=False
ENV=development
```

## 扩展指南

### 添加新的论文源

```python
from src.retrieval.paper_sources import PaperSource

class MyPaperSource(PaperSource):
    def search(self, query, top_k=10):
        # 实现搜索逻辑
        pass
    
    def fetch_paper(self, paper_id):
        # 实现获取论文详情的逻辑
        pass

# 注册到管理器
manager = PaperSourceManager()
manager.register_source("my_source", MyPaperSource())
```

### 自定义提示词

```python
from src.llm.prompts import PromptManager

# 添加自定义系统提示词
PromptManager.SYSTEM_PROMPTS["custom"] = "你是一个自定义的助手..."

# 添加自定义任务提示词
PromptManager.TASK_PROMPTS["custom_task"] = "自定义任务提示词 {param}"
```

### 扩展信息抽取

在 `PaperExtractor` 中添加自定义抽取逻辑：

```python
class CustomPaperExtractor(PaperExtractor):
    def _extract_custom_field(self, paper):
        # 自定义抽取逻辑
        pass
```

## 依赖项

- **核心依赖**:
  - openai: LLM API
  - flask: Web 框架
  - requests: HTTP 请求
  - numpy: 数值计算
  - pandas: 数据处理

- **可选依赖**:
  - sentence-transformers: 语义嵌入
  - faiss: 向量搜索
  - beautifulsoup4: 网页解析
  - PyPDF2: PDF 处理

## 测试

运行单元测试：

```bash
pytest tests/
```

运行特定测试：

```bash
pytest tests/test_intent.py -v
```

## 部署

### 本地开发

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API 密钥
python src/main.py
```

### Docker 部署

```bash
docker build -t ml-research-copilot .
docker run -p 5000:5000 ml-research-copilot
```

## API 使用示例

### 提交查询

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Transformer 在自然语言处理中的应用",
    "context": "我们需要了解注意力机制"
  }'
```

### 获取结果

```bash
curl http://localhost:5000/api/results/{query_id}
```

### 获取论文列表

```bash
curl http://localhost:5000/api/papers?query_id={query_id}
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

research@example.com
