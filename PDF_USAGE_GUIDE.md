"""
PDF 处理功能 - 使用指南
"""

# PDF 处理工作流示例

## 1. 基础使用：处理单篇论文

```python
from src.pdf_management import PDFProcessor
from src.llm.client import LLMClient

# 初始化
llm_client = LLMClient()  # 使用 OpenAI API
pdf_processor = PDFProcessor(
    cache_dir="./cache/pdfs",
    llm_client=llm_client,
)

# 处理单篇论文
paper = {
    "paper_id": "arxiv.2301.001",
    "title": "Example Paper",
    "url": "https://arxiv.org/pdf/2301.00001.pdf",
}

result = pdf_processor.process_paper(paper)
print(result)
# 输出:
# {
#     "success": True,
#     "paper_id": "arxiv.2301.001",
#     "pdf_path": "./cache/pdfs/arxiv.2301.001.pdf",
#     "extracted_info": ExtractedInfo(...),
#     "citations": [...],
#     "error": None,
# }
```

## 2. 批量处理论文

```python
papers = [
    {"paper_id": "arxiv.2301.001", "url": "..."},
    {"paper_id": "arxiv.2301.002", "url": "..."},
    {"paper_id": "arxiv.2301.003", "url": "..."},
]

results = pdf_processor.process_papers_batch(papers)
print(f"成功: {results['successful']}/{results['total']}")
# 输出:
# 成功: 3/3
```

## 3. 使用集成适配器丰富论文信息

```python
from src.pdf_management.integration import PDFIntegrationAdapter

adapter = PDFIntegrationAdapter(llm_client=llm_client)

# 单篇论文丰富
enriched_paper = adapter.enrich_paper_with_pdf(paper)
print(enriched_paper["pdf_content"]["sections"])
# 输出:
# {
#     "abstract": "...",
#     "methodology": "...",
#     "results": "...",
#     "conclusion": "...",
# }

# 批量论文丰富
enriched_papers = adapter.enrich_papers_batch(papers)
```

## 4. 生成论文总结

```python
# 从 PDF 内容生成详细总结
summary = adapter.generate_synthesis_from_pdf(enriched_paper)
print(summary)
```

## 5. 缓存管理

```python
from src.pdf_management import CacheManager

cache = CacheManager(cache_dir="./cache/pdfs")

# 检查缓存
if cache.has_cached_pdf("arxiv.2301.001"):
    print("论文已在本地缓存")

# 获取缓存统计
stats = cache.get_cache_stats()
print(f"缓存大小: {stats['total_size_mb']} MB")
print(f"缓存论文数: {stats['total_papers']}")

# 清理缓存（删除 30 天前的论文）
cache.cleanup(max_age_days=30, max_size_mb=5000)
```

## 6. PDF 下载和解析

```python
from src.pdf_management import PDFDownloader, PDFParser

# 下载器
downloader = PDFDownloader(cache_dir="./cache/pdfs")
result = downloader.download_paper("https://arxiv.org/pdf/2301.00001.pdf")

if result["success"]:
    pdf_path = result["file_path"]
    
    # 解析器
    parser = PDFParser(llm_client=llm_client)
    
    # 提取文本
    pages = parser.extract_text(pdf_path)
    print(f"提取了 {len(pages)} 页")
    
    # 解析结构
    sections = parser.parse_structure(pages)
    for section in sections:
        print(f"- {section.title} (第 {section.start_page}-{section.end_page} 页)")
    
    # 提取引用
    citations = parser.extract_citations(pages)
    print(f"发现 {len(citations)} 条引用")
```

## 7. 与主系统集成

```python
from src.main import ResearchEngine
from src.pdf_management.integration import PDFIntegrationAdapter

# 初始化研究引擎
engine = ResearchEngine()
pdf_adapter = PDFIntegrationAdapter(llm_client=engine.llm_client)

# 执行搜索
results = engine.process_query("machine learning optimization algorithms")

# 丰富搜索结果
papers = results.get("papers", [])
enriched_papers = pdf_adapter.enrich_papers_batch(papers, extract_pdf=True)

# 生成综合总结（使用 PDF 内容）
for paper in enriched_papers:
    if paper.get("pdf_processed"):
        summary = pdf_adapter.generate_synthesis_from_pdf(paper)
        print(f"{paper['title']}")
        print(f"总结: {summary}")
        print()
```

## 8. 配置和优化

```python
# 自定义缓存策略
cache = CacheManager(
    cache_dir="./cache/pdfs",
    max_papers=1000,  # 最多缓存 1000 篇
    cleanup_interval_hours=24,  # 每 24 小时清理一次
)

# 自定义下载配置
downloader = PDFDownloader(
    cache_dir="./cache/pdfs",
    max_workers=8,  # 最多 8 个并发下载
    timeout=60,  # 60 秒超时
    max_retries=5,  # 最多重试 5 次
)

# 处理时显示进度
def progress_callback(paper_id, downloaded, total):
    print(f"进度: {paper_id} - {downloaded}/{total} MB")

results = downloader.download_papers_batch(papers, progress_callback=progress_callback)
```

## 9. 错误处理

```python
try:
    result = pdf_processor.process_paper(paper)
    
    if result["success"]:
        print(f"成功处理: {result['paper_id']}")
        info = result["extracted_info"]
        print(f"标题: {info.title}")
        print(f"摘要: {info.abstract}")
    else:
        print(f"处理失败: {result['error']}")
        
except Exception as e:
    print(f"异常: {e}")
```

## 10. 文件结构

```
src/pdf_management/
├── __init__.py              # 模块入口
├── cache_manager.py         # 缓存管理
├── downloader.py            # PDF 下载
├── parser.py                # PDF 解析
├── pdf_processor.py         # 工作流处理
└── integration.py           # 与主系统集成
```

## 主要类和方法

### CacheManager
- `has_cached_pdf(paper_id)` - 检查缓存
- `register_pdf(paper_id, url, file_path, file_size)` - 注册
- `get_cache_path(paper_id)` - 获取路径
- `get_cache_stats()` - 统计信息
- `cleanup(max_age_days, max_size_mb)` - 清理

### PDFDownloader
- `download_paper(url)` - 下载单个
- `download_papers_batch(papers, progress_callback)` - 批量下载
- `get_download_stats()` - 统计

### PDFParser
- `extract_text(pdf_path)` - 提取文本
- `parse_structure(pages)` - 解析结构
- `extract_key_information(pdf_path, sections)` - 提取关键信息
- `extract_citations(pages)` - 提取引用

### PDFProcessor
- `process_paper(paper, force_reprocess)` - 处理单个
- `process_papers_batch(papers, force_reprocess)` - 批量处理
- `get_cache_stats()` - 缓存统计
- `cleanup_cache(max_age_days, max_size_mb)` - 清理

### PDFIntegrationAdapter
- `enrich_paper_with_pdf(paper, extract_pdf)` - 丰富论文
- `enrich_papers_batch(papers, extract_pdf)` - 批量丰富
- `generate_synthesis_from_pdf(paper, synthesis_prompt)` - 生成总结

## 特性

✅ **并发下载** - ThreadPoolExecutor 支持并发下载
✅ **自动重试** - 指数退避重试策略
✅ **PDF 验证** - 检查文件完整性
✅ **智能缓存** - 元数据跟踪、版本控制、增量更新
✅ **自动清理** - 基于时间和大小的清理策略
✅ **LLM 集成** - 使用 LLM 进行智能解析
✅ **结构解析** - 识别章节标题和内容
✅ **引用提取** - 自动提取参考文献
✅ **易于集成** - 与主系统无缝集成
"""

# 这是一个说明文档，不是可执行代码
# 请参考上面的示例进行集成
