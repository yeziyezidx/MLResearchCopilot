# PDF 处理功能 - 快速参考卡片

## 🎯 快速使用

### 1. 初始化
```python
from src.pdf_management import PDFProcessor
processor = PDFProcessor(llm_client=llm_client)
```

### 2. 处理论文
```python
result = processor.process_paper({
    "paper_id": "arxiv.2301.001",
    "url": "https://arxiv.org/pdf/2301.00001.pdf"
})
```

### 3. 批量处理
```python
results = processor.process_papers_batch(papers)
```

## 📦 核心类

| 类 | 文件 | 用途 |
|-----|------|------|
| `PDFDownloader` | `downloader.py` | 下载 PDF |
| `CacheManager` | `cache_manager.py` | 管理缓存 |
| `PDFParser` | `parser.py` | 解析内容 |
| `PDFProcessor` | `pdf_processor.py` | 工作流 |
| `PDFIntegrationAdapter` | `integration.py` | 系统集成 |

## 🔑 关键方法

### PDFDownloader
```python
download_paper(url)              # 下载单个
download_papers_batch(papers)    # 批量下载
get_download_stats()             # 统计信息
```

### CacheManager
```python
register_pdf(paper_id, ...)      # 注册 PDF
has_cached_pdf(paper_id)         # 检查缓存
get_cache_stats()                # 缓存统计
cleanup(max_age_days, ...)       # 清理缓存
```

### PDFParser
```python
extract_text(pdf_path)           # 提取文本
parse_structure(pages)           # 解析结构
extract_key_information(...)     # 提取信息
extract_citations(pages)         # 提取引用
```

### PDFProcessor
```python
process_paper(paper)             # 处理单篇
process_papers_batch(papers)     # 批量处理
get_cache_stats()                # 缓存统计
cleanup_cache(...)               # 清理缓存
```

### PDFIntegrationAdapter
```python
enrich_paper_with_pdf(paper)     # 丰富论文
enrich_papers_batch(papers)      # 批量丰富
generate_synthesis_from_pdf(...) # 生成总结
get_cache_stats()                # 缓存统计
```

## 💻 常见任务

### 任务 1: 下载论文
```python
from src.pdf_management import PDFDownloader
downloader = PDFDownloader()
result = downloader.download_paper(url)
if result["success"]:
    print(f"已保存: {result['file_path']}")
```

### 任务 2: 检查缓存
```python
from src.pdf_management import CacheManager
cache = CacheManager()
if cache.has_cached_pdf(paper_id):
    path = cache.get_cache_path(paper_id)
```

### 任务 3: 解析 PDF
```python
from src.pdf_management import PDFParser
parser = PDFParser()
pages = parser.extract_text(pdf_path)
sections = parser.parse_structure(pages)
```

### 任务 4: 完整处理
```python
from src.pdf_management import PDFProcessor
processor = PDFProcessor()
result = processor.process_paper(paper)
info = result["extracted_info"]
```

### 任务 5: 丰富论文信息
```python
from src.pdf_management.integration import PDFIntegrationAdapter
adapter = PDFIntegrationAdapter()
enriched = adapter.enrich_paper_with_pdf(paper)
```

### 任务 6: 生成总结
```python
summary = adapter.generate_synthesis_from_pdf(enriched_paper)
```

## ⚙️ 配置

```python
# CacheManager 配置
CacheManager(
    cache_dir="./cache/pdfs",
    max_papers=1000,
)

# PDFDownloader 配置
PDFDownloader(
    cache_dir="./cache/pdfs",
    max_workers=4,           # 并发数
    timeout=30,              # 超时秒
    max_retries=3,           # 重试次数
)

# PDFProcessor 配置
PDFProcessor(
    cache_dir="./cache/pdfs",
    llm_client=llm,
    max_workers=4,
)

# PDFParser 配置
PDFParser(
    llm_client=llm,  # 可选
)
```

## 📊 返回值

### download_paper() 返回
```python
{
    "success": bool,
    "file_path": str,
    "file_size": int,
    "error": str,
}
```

### process_paper() 返回
```python
{
    "success": bool,
    "paper_id": str,
    "pdf_path": str,
    "extracted_info": ExtractedInfo,
    "citations": List[str],
    "error": str,
}
```

### get_cache_stats() 返回
```python
{
    "total_papers": int,
    "total_size_mb": float,
}
```

## 🛠️ 安装依赖

```bash
pip install PyPDF2>=3.0.0 pdfplumber>=0.9.0
```

或使用 requirements.txt:
```bash
pip install -r requirements.txt
```

## 📚 文档链接

- **完整指南**: `PDF_USAGE_GUIDE.md`
- **实现细节**: `PDF_IMPLEMENTATION.md`
- **功能说明**: `PDF_FEATURES.md`
- **示例代码**: `examples/pdf_integration_example.py`
- **测试用例**: `tests/test_pdf_module.py`

## 🎯 典型工作流

```
1. 获取搜索结果 (URL + 元数据)
   ↓
2. 检查缓存 (避免重复下载)
   ↓
3. 下载 PDF (并发, 重试)
   ↓
4. 注册缓存 (记录元数据)
   ↓
5. 提取内容 (文本 + 结构)
   ↓
6. LLM 分析 (生成摘要)
   ↓
7. 返回结果 (丰富的论文数据)
```

## 🚨 错误处理

```python
try:
    result = processor.process_paper(paper)
    if result["success"]:
        print("成功")
    else:
        print(f"失败: {result['error']}")
except Exception as e:
    print(f"异常: {e}")
```

## 💡 最佳实践

1. **使用缓存** - 避免重复下载
2. **批量处理** - 使用并发提高速度
3. **定期清理** - 使用 cleanup() 管理磁盘空间
4. **错误处理** - 总是检查 success 标志
5. **LLM 集成** - 为了更好的分析，提供 llm_client
6. **监控统计** - 定期检查缓存状态

## 🔗 集成示例

```python
# 在研究引擎中集成
from src.main import ResearchEngine
from src.pdf_management.integration import PDFIntegrationAdapter

engine = ResearchEngine()
adapter = PDFIntegrationAdapter(llm_client=engine.llm_client)

# 搜索并丰富
results = engine.process_query("query")
papers = results.get("papers", [])
enriched = adapter.enrich_papers_batch(papers, extract_pdf=True)

# 生成总结
for paper in enriched:
    if paper.get("pdf_processed"):
        summary = adapter.generate_synthesis_from_pdf(paper)
```

---

**快速参考版本**: 1.0  
**最后更新**: 2024  
**维护**: 开发团队
