# ML Research Copilot

一个智能研究辅助系统，帮助用户进行文献综合分析和研究问题解答。

## 系统架构

```
用户问题
   ↓
Research 意图理解 [LLM]
   ↓
关键词抽取 [LLM]
   ↓
关键概念理解 [Web Search]
   ↓
领域问题构建 [LLM]
   ↓
语义检索 [Retrieval Model]
   ↓
候选论文 (Top-K)
   ↓
结构化信息抽取 [LLM]
   ↓
模型并行处理论文
   ↓
表格化展示 [Spreadsheet UI]
   ↓
跨论文聚合与综合 [LLM]
   ↓
引用溯源
   ↓
用户交互编辑
```

## 项目结构

```
MLResearchCopilot/
├── src/
│   ├── __init__.py
│   ├── main.py                 # 主入口
│   ├── config.py               # 配置管理
│   ├── core/
│   │   ├── __init__.py
│   │   ├── intent_understanding.py      # 意图理解模块
│   │   ├── keyword_extraction.py        # 关键词抽取
│   │   ├── concept_understanding.py     # 概念理解
│   │   └── problem_formulation.py       # 问题构建
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── semantic_search.py           # 语义检索
│   │   ├── paper_sources.py             # 论文来源管理(arXiv, ACL, GitHub)
│   │   └── retriever.py                 # 检索器
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── paper_extractor.py           # 论文信息抽取
│   │   ├── structured_output.py         # 结构化输出
│   │   └── metadata.py                  # 元数据定义
│   ├── synthesis/
│   │   ├── __init__.py
│   │   ├── aggregator.py                # 跨论文聚合
│   │   ├── citation_tracking.py         # 引用溯源
│   │   └── summarizer.py                # 多文档综合
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py                    # LLM 客户端
│   │   ├── prompts.py                   # 提示词模板
│   │   └── utils.py                     # 工具函数
│   └── ui/
│       ├── __init__.py
│       ├── web_app.py                   # Web 应用
│       ├── api.py                       # REST API
│       └── templates/
│           ├── index.html
│           ├── results.html
│           └── static/
├── tests/
│   ├── __init__.py
│   ├── test_intent.py
│   ├── test_extraction.py
│   └── test_synthesis.py
├── requirements.txt
├── .env.example
├── setup.py
└── README.md
```

## 主要功能模块

### 1. 核心理解模块 (core/)
- **意图理解**: 分析用户问题，理解研究意图
- **关键词抽取**: 提取关键词、论文名称、方法术语
- **概念理解**: 通过网络搜索理解关键概念
- **问题构建**: 构建结构化的域问题

### 2. 检索模块 (retrieval/)
- **语义检索**: 从多个来源检索相关论文
- **论文源管理**: 支持 arXiv、ACL、GitHub、Hugging Face
- **检索器**: 整合多源检索

### 3. 信息抽取模块 (extraction/)
- **论文抽取**: 从论文中抽取标题、摘要、方法、结果等
- **结构化输出**: 生成统一的数据格式
- **元数据管理**: 定义论文的结构化字段

### 4. 综合分析模块 (synthesis/)
- **聚合器**: 跨论文信息聚合
- **引用溯源**: 进行句子级别的引用跟踪
- **多文档总结**: LLM 进行跨论文综合总结

### 5. LLM 集成模块 (llm/)
- **客户端**: 集成 OpenAI、本地模型等
- **提示词**: 优化的系统提示和任务提示
- **工具函数**: LLM 调用的辅助函数

### 6. 用户界面模块 (ui/)
- **Web 应用**: Flask/FastAPI Web 界面
- **REST API**: 后端 API 接口
- **表格展示**: 论文信息的表格化展示
- **交互编辑**: 用户可编辑、筛选、删除论文

## 快速开始

### 环境要求
- Python 3.9+
- pip

### 安装

```bash
git clone <repository-url>
cd MLResearchCopilot
pip install -r requirements.txt
```

### 配置

1. 复制 `.env.example` 为 `.env`
2. 配置 API 密钥（OpenAI、Semantic Scholar等）

```bash
OPENAI_API_KEY=your_key_here
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

### 运行

```bash
python src/main.py
```

访问 `http://localhost:5000` 打开 Web 界面。

## 使用示例

```python
from src.core.intent_understanding import IntentUnderstanding
from src.retrieval.retriever import Retriever
from src.extraction.paper_extractor import PaperExtractor
from src.synthesis.summarizer import Summarizer

# 1. 理解用户问题
intent = IntentUnderstanding().understand("如何使用 Transformer 进行机器翻译?")

# 2. 提取关键词
keywords = intent.extract_keywords()

# 3. 检索论文
retriever = Retriever()
papers = retriever.search(keywords, top_k=10)

# 4. 抽取信息
extractor = PaperExtractor()
structured_papers = [extractor.extract(paper) for paper in papers]

# 5. 综合分析
summarizer = Summarizer()
summary = summarizer.synthesize(structured_papers)
```

## API 端点

- `POST /api/query` - 提交研究问题
- `GET /api/results/<query_id>` - 获取检索结果
- `POST /api/papers` - 手动添加论文
- `PUT /api/papers/<paper_id>` - 编辑论文信息
- `DELETE /api/papers/<paper_id>` - 删除论文
- `GET /api/summary` - 获取综合总结

## 技术栈

- **LLM 集成**: OpenAI API, LangChain
- **检索**: Semantic Scholar, arXiv API, Hugging Face
- **Web 框架**: Flask / FastAPI
- **数据处理**: Pandas, SQLAlchemy
- **向量数据库**: Faiss / Pinecone
- **文档处理**: PyPDF2, BeautifulSoup4

## 许可证

MIT License

## 联系方式

有任何问题或建议，欢迎提交 Issue 或 Pull Request。
