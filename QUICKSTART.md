# 快速开始指南

## 前置要求

- Python 3.9+
- pip 包管理器
- 互联网连接（用于 API 调用）

## 安装步骤

### 1. 克隆或下载项目

```bash
cd MLResearchCopilot
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，添加你的 API 密钥
# 使用任何文本编辑器打开 .env
```

**必需的配置**：
- `OPENAI_API_KEY`: 从 [OpenAI](https://platform.openai.com/api-keys) 获取
- `OPENAI_MODEL`: 默认为 "gpt-4"（可选：使用 "gpt-3.5-turbo"）

**可选的配置**：
- `SEMANTIC_SCHOLAR_API_KEY`: 从 [Semantic Scholar](https://www.semanticscholar.org/) 获取
- `HUGGINGFACE_TOKEN`: 从 [Hugging Face](https://huggingface.co/) 获取

## 运行系统

### 方式 1：Web 应用

```bash
python src/main.py
```

然后在浏览器中打开 `http://localhost:5000`

### 方式 2：命令行测试

编辑 `src/main.py` 中的 `if __name__ == "__main__"` 部分，修改测试查询：

```python
test_query = "你的研究问题"
query_id = engine.process_query(test_query)
```

然后运行：

```bash
python src/main.py
```

## 使用示例

### 1. 通过 Web 界面

1. 打开 `http://localhost:5000`
2. 在输入框中输入你的研究问题，例如：
   ```
   如何使用 Transformer 进行机器翻译？
   ```
3. （可选）添加背景信息
4. 点击"分析问题并搜索论文"
5. 系统将自动处理并显示结果

### 2. 通过 Python 代码

```python
from src.main import ResearchEngine
from src.config import get_config

# 初始化引擎
config = get_config()
engine = ResearchEngine(config)

# 处理查询
query_id = engine.process_query(
    query="Transformer 在自然语言处理中的应用",
    context="我们需要了解注意力机制的原理"
)

# 获取结果
results = engine.get_results(query_id)

# 访问不同的结果部分
papers = results.get('papers', [])
synthesis = results.get('synthesis', {})
aggregation = results.get('aggregation', {})

# 打印结果
print(f"检索到 {len(papers)} 篇论文")
print(f"综合总结：{synthesis.get('summary', '')}")
```

### 3. 通过 REST API

```bash
# 提交查询
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "深度学习中的优化方法",
    "context": "特别关注 Adam 优化器"
  }'

# 响应示例
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}

# 获取结果（每隔 2 秒检查一次）
curl http://localhost:5000/api/results/550e8400-e29b-41d4-a716-446655440000
```

## 项目结构说明

```
MLResearchCopilot/
├── src/                          # 源代码
│   ├── core/                     # 核心理解模块
│   │   ├── intent_understanding.py
│   │   ├── keyword_extraction.py
│   │   ├── concept_understanding.py
│   │   └── problem_formulation.py
│   ├── retrieval/                # 检索模块
│   │   ├── semantic_search.py
│   │   ├── paper_sources.py
│   │   └── retriever.py
│   ├── extraction/               # 信息抽取模块
│   │   ├── paper_extractor.py
│   │   ├── structured_output.py
│   │   └── metadata.py
│   ├── synthesis/                # 综合分析模块
│   │   ├── aggregator.py
│   │   ├── citation_tracking.py
│   │   └── summarizer.py
│   ├── llm/                      # LLM 集成
│   │   ├── client.py
│   │   ├── prompts.py
│   │   └── utils.py
│   ├── ui/                       # Web UI
│   │   ├── web_app.py
│   │   ├── api.py
│   │   └── templates/
│   ├── config.py                 # 配置管理
│   └── main.py                   # 主入口
├── tests/                        # 单元测试
│   ├── test_intent.py
│   ├── test_extraction.py
│   └── test_synthesis.py
├── requirements.txt              # 依赖列表
├── setup.py                      # 安装脚本
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git 忽略文件
├── README.md                     # 项目说明
└── ARCHITECTURE.md               # 架构文档
```

## 常见问题

### Q: 没有 OpenAI API 密钥怎么办？

A: 系统会使用模拟响应。虽然功能有限，但你可以测试基本的流程。需要完整功能，请获取 API 密钥。

### Q: 如何使用本地 LLM 模型？

A: 修改 `src/config.py` 中的 `OPENAI_BASE_URL`：

```python
OPENAI_BASE_URL = "http://localhost:8000/v1"  # 本地模型 API 地址
```

### Q: 如何添加新的论文源？

A: 在 `src/retrieval/paper_sources.py` 中创建新类：

```python
from src.retrieval.paper_sources import PaperSource

class MySource(PaperSource):
    def search(self, query, top_k=10):
        # 实现搜索逻辑
        pass
    
    def fetch_paper(self, paper_id):
        # 实现获取详情逻辑
        pass
```

然后在 `PaperSourceManager` 中注册：

```python
manager.register_source("my_source", MySource())
```

### Q: 如何运行单元测试？

A: 

```bash
pip install pytest
pytest tests/ -v
```

### Q: 如何部署到生产环境？

A: 查看 `ARCHITECTURE.md` 中的部署指南，或创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/main.py"]
```

## 性能优化建议

1. **使用更好的嵌入模型**: 
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   ```

2. **添加缓存**:
   ```python
   import functools
   @functools.lru_cache(maxsize=128)
   def cached_embedding(text):
       return get_embedding(text)
   ```

3. **并行处理论文**:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   with ThreadPoolExecutor(max_workers=4) as executor:
       results = list(executor.map(extract_paper, papers))
   ```

4. **使用向量数据库**:
   - Faiss: 本地高效搜索
   - Pinecone: 云端向量数据库
   - Weaviate: 开源向量数据库

## 下一步

1. **配置 API 密钥**: 编辑 `.env` 文件
2. **运行系统**: 执行 `python src/main.py`
3. **测试查询**: 在 Web 界面上输入研究问题
4. **查看文档**: 阅读 `ARCHITECTURE.md` 了解详细设计
5. **扩展功能**: 根据需要自定义模块

## 获取帮助

- 查看 `ARCHITECTURE.md` 了解系统设计
- 查看 `README.md` 了解功能概述
- 查看源代码中的 docstring 了解函数使用
- 运行测试了解预期行为

## 许可证

MIT License - 详见 LICENSE 文件

---

祝你使用愉快！如有任何问题，欢迎反馈。
