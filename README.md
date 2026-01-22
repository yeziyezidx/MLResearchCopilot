# ML Research Copilot

一个智能研究辅助系统，帮助用户进行文献综合分析和研究问题解答。

## 系统架构

系统采用**6层模块化架构**，支持端到端的学术研究问题解答：

```
用户问题 (自然语言)
   ↓
[1] Research 意图理解 [LLM + 模板系统]
    ├─ 提取：意图类型、研究领域、关键主题、研究问题
    └─ 输出：多个子问题
   ↓
[2] 广泛答案生成 [Web搜索 + LLM综合]
    ├─ 搜索：DuckDuckGo/Google/Bing API/Bing Grounding
    ├─ 综合：LLM融合搜索结果和知识库
    └─ 输出：研究背景、研究领域的workflow、用于搜索paper的学术query
   ↓
[3] 语义检索 [多源检索]
    ├─ 来源：arXiv、ACL、GitHub、Hugging Face、web
    └─ 输出：Top-K相关学术论文
   ↓
[4] 论文处理管道 [LLM + PDF处理]
    ├─ PDF下载与缓存管理
    ├─ PDF文本提取与解析
    └─ LLM结构化信息抽取
   ↓
[5] 跨论文聚合与综合 [LLM多文档总结]
    ├─ 信息聚合（去重、融合）
    ├─ 跨论文关联
    └─ 综合总结与核心发现
   ↓
[6] 用户交互与展示 [Web UI]
    ├─ 结构化表格展示
    ├─ 交互式编辑与筛选
    └─ 引用管理与导出
```

## 项目结构

```
MLResearchCopilot/
├── src/
│   ├── __init__.py
│   ├── main.py                 # 主入口 - ResearchEngine 核心引擎
│   ├── config.py               # 配置管理
│   ├── core/                   # 核心理解与生成模块
│   │   ├── __init__.py
│   │   ├── intent_understanding.py      # 研究意图理解（LLM+模板）
│   │   ├── broad_answer_generation.py   # 广泛答案生成（Web搜索+LLM综合）
│   │   ├── concept_understanding.py     # 概念理解
│   │   ├── problem_formulation.py       # 问题构建
│   │   └── web_search.py                # Web搜索工具（DuckDuckGo/Google/Bing）
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── semantic_search.py           # 语义检索（学术论文库）
│   │   ├── paper_sources.py             # 论文来源管理(arXiv, ACL, GitHub, Hugging Face)
│   │   └── retriever.py                 # 多源检索器
│   ├── pdf_management/                  # PDF 处理与管理（新增）
│   │   ├── __init__.py
│   │   ├── cache_manager.py             # PDF 缓存管理
│   │   ├── downloader.py                # 并发 PDF 下载器
│   │   ├── parser.py                    # PDF 文本提取与解析
│   │   ├── pdf_processor.py             # PDF 工作流编排
│   │   └── integration.py               # PDF 与系统集成适配器
│   ├── synthesis/
│   │   ├── __init__.py
│   │   ├── aggregator.py                # 跨论文信息聚合
│   │   └── summarizer.py                # 多文档综合总结
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py                    # LLM 客户端（OpenAI/Papyrus/Azure，带速率限制）
│   │   └── utils.py                     # 工具函数
│   ├── slm/                             # 轻量级模型模块（可选）
│   │   ├── __init__.py
│   │   └── ...
│   └── ui/
│       ├── __init__.py
│       ├── web_app.py                   # Flask Web 应用
│       ├── api.py                       # REST API
│       └── templates/
│           ├── index.html
│           ├── results.html
│           └── static/
├── tests/
│   ├── __init__.py
│   ├── test_pdf_module.py
│   ├── debugger.py              # Debug 日志工具
│   └── ...
├── examples/
│   ├── broad_answer_with_web_search_example.py
│   └── ...
├── docs/
│   ├── BROAD_ANSWER_WEB_SEARCH.md
│   ├── PDF_USAGE_GUIDE.md
│   └── ...
├── requirements.txt
├── .env.example
├── launch.json                  # VS Code 调试配置
└── README.md
```

## 主要功能模块

### 1. 核心理解与生成模块 (core/)
- **意图理解** (`intent_understanding.py`): 分析用户问题，使用LLM提取研究意图类型、研究领域、关键主题、研究问题（支持双语输出）
- **广泛答案生成** (`broad_answer_generation.py`): 集成Web搜索（DuckDuckGo/Google/Bing）+ LLM综合，生成最新、全面的答案
- **概念理解** (`concept_understanding.py`): 通过网络搜索理解关键概念
- **问题构建** (`problem_formulation.py`): 构建结构化的域问题
- **Web搜索工具** (`web_search.py`): 支持DuckDuckGo（免费）、Google Custom Search、Bing Search、Bing Grounding (https://groundingportalui-ejgvfydefkh4d9ha.canadacentral-01.azurewebsites.net/) 等多个搜索引擎

### 2. 检索模块 (retrieval/)
- **语义检索** (`semantic_search.py`): 从多个学术源检索相关论文
- **论文源管理** (`paper_sources.py`): 支持arXiv、ACL Anthology、GitHub、Hugging Face等多源
- **检索器** (`retriever.py`): 整合多源检索，返回Top-K相关论文

### 3. PDF管理模块 (pdf_management/) - 增强型
- **缓存管理** (`cache_manager.py`): 本地PDF缓存，版本控制，增量更新
- **并发下载** (`downloader.py`): 多线程PDF下载，重试机制，超时控制
- **PDF解析** (`parser.py`): 文本提取、结构识别、引用提取、LLM分析
- **工作流处理** (`pdf_processor.py`): 完整的下载→缓存→解析→提取流程
- **系统集成** (`integration.py`): 将PDF内容集成到论文提取和综合分析流程

### 4. 综合分析模块 (synthesis/)
- **聚合器** (`aggregator.py`): 跨论文信息聚合，去重、融合
- **总结器** (`summarizer.py`): 多文档LLM综合总结，生成研究综述

### 5. LLM集成模块 (llm/)
- **客户端** (`client.py`): 支持OpenAI、Papyrus（Bing内部）、Azure Cognitive Services，集成速率限制(REQUEST_DELAY)
- **工具函数** (`utils.py`): LLM调用的辅助函数、提示词处理

### 6. 提示词模板管理 (templates/) - 可扩展
- **TemplateLoader**: 从JSON文件动态加载LLM提示词模板
- **内置模板**: 意图分析、论文提取、答案综合、研究综合等
- 支持动态变量替换，易于维护和自定义

### 7. 用户界面模块 (ui/)
- **Web应用** (`web_app.py`): Flask Web界面
- **REST API** (`api.py`): 后端API接口
- **表格展示**: 论文信息的表格化展示
- **交互编辑**: 用户可编辑、筛选、删除论文

## 快速开始

### 环境要求
- Python 3.9+
- conda 或 pip + venv

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd MLResearchCopilot

# 方式1: 使用 Conda（推荐）
conda create -n research_copilot python=3.10 -y
conda activate research_copilot
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 方式2: 使用 venv
python -m venv .venv_research_copilot
# Windows
.\.venv_research_copilot\Scripts\Activate.ps1
# macOS/Linux
source .venv_research_copilot/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 配置

1. 复制 `.env.example` 为 `.env`

```bash
cp .env.example .env
```

2. 配置必需的API密钥和环境变量

```bash
# OpenAI 配置
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Web搜索配置（选择至少一个）
Speedbird_SEARCH_API_KEY=your_bing_key          # Bing Grounding索（推荐）
GOOGLE_API_KEY=your_google_key              # Google 搜索以及Gemma3 embedding

# Papyrus/Azure（可选）
PROVIDER=openai                             # 或 "papyrus"
AZURE_CREDENTIAL=...
PAPYRUS_QUOTA_ID=...
PAPYRUS_MODEL_NAME=...
```

3. VS Code调试配置（`.vscode/launch.json`）

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Debug Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/main.py",
            "console": "integratedTerminal",
            "env": {
                "OPENAI_API_KEY": "your_key_here",
                "BING_SEARCH_API_KEY": "your_bing_key_here"
            }
        }
    ]
}
```

### 运行

```bash
# 启动主程序
python src/main.py

# 或使用Flask开发服务器
cd src/ui
python web_app.py

# 访问 http://localhost:5000
```

## 使用示例

### 基本流程示例

```python
from src.main import ResearchEngine
from src.config import get_config

# 初始化引擎
config = get_config()
engine = ResearchEngine(config, enable_debug=True)  # 启用调试日志

# 处理用户问题
query = "深度研究系统如何从检索到的网页中进行细粒度证据抽取？"
query_id = engine.process_query(query)

# Debug日志保存在：./debug_logs/<timestamp>/
```

### 单模块使用示例

#### 意图理解
```python
from src.core.intent_understanding import IntentUnderstanding
from src.llm.client import LLMClient

llm_client = LLMClient(provider="openai", model="gpt-4")
intent_analyzer = IntentUnderstanding(llm_client)

query = "Transformer模型在机器翻译中的应用"
intent = intent_analyzer.understand(query)

print(f"意图类型: {intent.intent_type}")
print(f"研究领域: {intent.research_area}")
print(f"研究问题: {intent.research_questions}")
```

#### 广泛答案生成（带Web搜索）
```python
from src.core.broad_answer_generation import BroadAnswerGenerator

generator = BroadAnswerGenerator(
    llm_client=llm_client,
    enable_web_search=True,
    num_search_results=5
)

# 生成答案（包含网络搜索）
answer = generator.generate("最新的LLM发展趋势是什么？")

print(f"答案摘要: {answer.summary}")
print(f"关键概念: {answer.key_concepts}")
print(f"最新发展: {answer.recent_developments}")
print(f"权威来源: {answer.authoritative_sources}")
```

#### 论文检索
```python
from src.retrieval.retriever import Retriever

retriever = Retriever()
papers = retriever.search(
    keywords=["Transformer", "attention mechanism"],
    sources=["arxiv", "acl"],
    top_k=10
)

for paper in papers:
    print(f"- {paper['title']} ({paper['source']})")
```

#### PDF处理管道
```python
from src.pdf_management.pdf_processor import PDFProcessor

processor = PDFProcessor(
    enable_cache=True,
    num_workers=3,  # 并发下载数
)

# 下载、缓存、解析PDF
results = processor.process_papers([
    {"url": "https://..../paper1.pdf", "title": "Paper 1"},
    {"url": "https://..../paper2.pdf", "title": "Paper 2"},
])

for result in results:
    print(f"提取文本: {result['extracted_text'][:200]}...")
```

#### Web搜索
```python
from src.core.web_search import get_searcher

# 自动选择可用的搜索引擎（Bing > Google > DuckDuckGo）
searcher = get_searcher(prefer_bing=True)

results = searcher.search("latest developments in large language models", num_results=5)

for i, result in enumerate(results, 1):
    print(f"{i}. {result.title}")
    print(f"   {result.url}")
    print(f"   {result.snippet}\n")
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/query` | POST | 提交研究问题，返回query_id |
| `/api/results/<query_id>` | GET | 获取查询结果（意图、答案、论文等） |
| `/api/debug/<query_id>` | GET | 获取调试日志路径 |
| `/api/papers` | GET | 列出所有检索到的论文 |
| `/api/papers/<paper_id>` | PUT | 编辑论文信息 |
| `/api/papers/<paper_id>` | DELETE | 删除论文 |
| `/api/summary` | GET | 获取当前查询的综合总结 |
| `/api/export` | POST | 导出结果为JSON/CSV/PDF |

## 配置文件说明

### requirements.txt

核心依赖：
- `openai>=1.0.0` - OpenAI API
- `requests>=2.31.0` - HTTP 请求
- `PyPDF2>=3.0.0`, `pdfplumber>=0.9.0` - PDF 处理
- `flask>=2.3.0` - Web 框架
- `pandas>=2.0.0` - 数据处理
- `azure-identity>=1.14.0` - Azure/Papyrus 认证

### .env 示例

```env
# LLM 配置
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
PROVIDER=openai  # 或 "papyrus"

# Web搜索配置
BING_SEARCH_API_KEY=...
BING_SEARCH_ENDPOINT=https://...cognitiveservices.azure.com/bing/v7.0/search

GOOGLE_API_KEY=...
GOOGLE_SEARCH_ENGINE_ID=...

# 可选：Papyrus配置
PAPYRUS_QUOTA_ID=...
PAPYRUS_MODEL_NAME=...
PAPYRUS_TIMEOUT_MS=100000

# PDF处理
PDF_DOWNLOAD_ENABLED=true
PDF_CACHE_DIR=./pdf_cache
PDF_CONCURRENT_WORKERS=3
```

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **LLM集成** | OpenAI API, Papyrus (Bing内部) | GPT-4, 支持Azure Cognitive Services |
| **Web搜索** | DuckDuckGo, Google Custom Search, Bing Search | 免费和付费选项 |
| **论文检索** | arXiv API, ACL Anthology, Semantic Scholar | 多源学术论文库 |
| **PDF处理** | PyPDF2, pdfplumber | PDF下载、缓存、解析 |
| **提示词管理** | JSON模板系统 | 可扩展、易维护的LLM提示词 |
| **Web框架** | Flask | 轻量级Web应用 |
| **数据处理** | Pandas, SQLAlchemy | 表格化展示、数据持久化 |
| **并发处理** | ThreadPoolExecutor | 批量PDF下载、API调用 |
| **速率限制** | 自实现 | 避免API频率限制 |
| **调试工具** | DebugLogger | JSON日志、中间结果保存 |

## 关键特性

✅ **多源论文检索** - arXiv、ACL、GitHub、Hugging Face  
✅ **Web搜索集成** - 最新信息融合（DuckDuckGo/Google/Bing）  
✅ **PDF全文处理** - 并发下载、缓存、智能解析  
✅ **模板化提示词** - JSON配置，易于自定义  
✅ **多LLM支持** - OpenAI、Papyrus、Azure  
✅ **速率限制** - 避免API限流  
✅ **双语支持** - 中英文输出  
✅ **调试日志** - 完整的中间过程追踪  
✅ **结构化输出** - 统一的数据格式  
✅ **交互式编辑** - Web UI中的结果编辑

## 文档

- [PDF使用指南](./docs/PDF_USAGE_GUIDE.md) - PDF处理管道详解
- [广泛答案生成](./docs/BROAD_ANSWER_WEB_SEARCH.md) - Web搜索+LLM综合
- [模板系统说明](./src/templates/README.md) - 提示词模板管理
- [API文档](./docs/API.md) - REST API详细说明

## 常见问题

### Q: 如何切换LLM提供商？
A: 修改 `.env` 中的 `PROVIDER` 或直接在代码中指定：
```python
llm_client = LLMClient(provider="papyrus")  # 使用Papyrus
```

### Q: 如何启用调试日志？
A: 在ResearchEngine初始化时启用：
```python
engine = ResearchEngine(config, enable_debug=True)
# 日志保存在 ./debug_logs/<timestamp>/
```

### Q: 如何自定义LLM提示词？
A: 编辑 `templates/` 目录中的JSON文件，或在代码中加载自定义模板：
```python
from templates import get_template_loader
loader = get_template_loader()
prompt = loader.get_prompt("intent_analysis", "user_prompt", query="...")
```

### Q: PDF处理性能如何优化？
A: 调整配置：
```env
PDF_CONCURRENT_WORKERS=10        # 增加并发数
PDF_CACHE_DIR=./fast_ssd_cache   # 使用快速存储
```

### Q: 支持哪些论文源？
A: 当前支持：arXiv、ACL Anthology、Semantic Scholar。可在 `src/retrieval/paper_sources.py` 中扩展。

## 贡献指南

欢迎PR！请：
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -m 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 提交Pull Request

## 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

## 联系与支持

- 提交Issue或Pull Request
- 邮件: [contact information]
- 文档: 见 `docs/` 目录
