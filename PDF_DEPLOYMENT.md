# PDF 处理功能 - 部署和集成指南

## 📋 前置准备

### 1. 环境要求
- Python 3.9+
- pip 包管理器
- 可选: OpenAI API 密钥 (用于 LLM 分析)

### 2. 依赖安装

#### 方法 A: 使用 requirements.txt (推荐)
```bash
pip install -r requirements.txt
```

#### 方法 B: 手动安装
```bash
pip install PyPDF2>=3.0.0 pdfplumber>=0.9.0
pip install requests>=2.31.0  # 已有
pip install openai>=1.0.0     # 已有
```

### 3. 验证安装
```python
import PyPDF2
import pdfplumber
from src.pdf_management import PDFProcessor
print("✓ PDF 模块已安装")
```

## 🔧 配置步骤

### 步骤 1: 创建缓存目录
```bash
# 手动创建
mkdir -p ./cache/pdfs

# 或在 Python 中
from pathlib import Path
Path("./cache/pdfs").mkdir(parents=True, exist_ok=True)
```

### 步骤 2: 环境变量配置

创建 `.env` 文件 (如果尚未存在):
```env
OPENAI_API_KEY=sk-...  # 您的 OpenAI API 密钥
PDF_CACHE_DIR=./cache/pdfs
PDF_MAX_WORKERS=4
PDF_TIMEOUT=30
```

### 步骤 3: 初始化系统
```python
from src.pdf_management import PDFProcessor
from src.llm.client import LLMClient
import os

# 配置
llm = LLMClient()
processor = PDFProcessor(
    cache_dir=os.getenv("PDF_CACHE_DIR", "./cache/pdfs"),
    llm_client=llm,
    max_workers=int(os.getenv("PDF_MAX_WORKERS", "4")),
)

print("✓ PDF 处理器已初始化")
```

## 🚀 集成步骤

### 步骤 1: 在主系统中导入
```python
# src/main.py 中添加
from src.pdf_management.integration import PDFIntegrationAdapter

class ResearchEngine:
    def __init__(self):
        # ... 现有初始化 ...
        self.pdf_adapter = PDFIntegrationAdapter(
            llm_client=self.llm_client,
        )
```

### 步骤 2: 更新搜索流程
```python
def process_query(self, query: str):
    # ... 现有搜索逻辑 ...
    papers = self.retriever.search(query)
    
    # 新增: 丰富论文信息
    enriched_papers = self.pdf_adapter.enrich_papers_batch(
        papers,
        extract_pdf=True,
    )
    
    return {
        "papers": enriched_papers,
        # ... 其他结果 ...
    }
```

### 步骤 3: 更新结果格式
```python
# 在返回结果时，检查是否有 PDF 内容
for paper in enriched_papers:
    if paper.get("pdf_processed"):
        paper["pdf_content_available"] = True
        paper["pdf_path"] = paper.get("pdf_path")
    else:
        paper["pdf_content_available"] = False
```

## 📱 API 端点集成 (Web UI)

### 步骤 1: 添加新的 REST 端点

```python
# src/web/app.py 中添加

@app.route("/api/research", methods=["POST"])
def research():
    data = request.json
    query = data.get("query")
    enable_pdf = data.get("enable_pdf", True)
    
    # 处理查询
    engine = ResearchEngine()
    results = engine.process_query(query)
    
    # 可选: 处理 PDF
    if enable_pdf:
        papers = results.get("papers", [])
        # PDF 处理已在主流程中
    
    return jsonify(results)

@app.route("/api/pdf/status", methods=["GET"])
def pdf_status():
    """获取 PDF 缓存状态"""
    engine = ResearchEngine()
    stats = engine.pdf_adapter.get_cache_stats()
    return jsonify(stats)

@app.route("/api/pdf/cleanup", methods=["POST"])
def pdf_cleanup():
    """清理过期 PDF"""
    data = request.json
    max_age = data.get("max_age_days", 30)
    max_size = data.get("max_size_mb", 5000)
    
    engine = ResearchEngine()
    engine.pdf_adapter.processor.cleanup_cache(max_age, max_size)
    
    return jsonify({"status": "cleaned"})
```

### 步骤 2: 更新前端显示

```html
<!-- 显示 PDF 可用性 -->
<div class="paper-item">
    <h3>{{ paper.title }}</h3>
    <p>{{ paper.abstract }}</p>
    
    {% if paper.pdf_processed %}
    <div class="pdf-content">
        <p><strong>完整分析:</strong></p>
        <p>{{ paper.pdf_content.sections.methodology }}</p>
        <button onclick="downloadPDF('{{ paper.pdf_path }}')">
            下载 PDF
        </button>
    </div>
    {% endif %}
</div>
```

## 🧪 测试集成

### 步骤 1: 单元测试
```bash
pytest tests/test_pdf_module.py -v
```

### 步骤 2: 集成测试
```python
# 创建 test_integration.py
from src.main import ResearchEngine

def test_pdf_integration():
    engine = ResearchEngine()
    results = engine.process_query("machine learning")
    
    papers = results.get("papers", [])
    assert len(papers) > 0
    
    # 检查是否有 PDF 内容
    for paper in papers[:3]:
        if paper.get("pdf_processed"):
            assert "pdf_content" in paper
            assert paper["pdf_content"]["sections"]["abstract"]

if __name__ == "__main__":
    test_pdf_integration()
    print("✓ 集成测试通过")
```

### 步骤 3: 手动测试
```python
# manual_test.py
from examples.pdf_integration_example import *

# 运行所有示例
main()
```

## 📊 监控和维护

### 定期检查

```python
# 每天运行
from src.pdf_management import CacheManager
from datetime import datetime

cache = CacheManager()
stats = cache.get_cache_stats()

print(f"[{datetime.now()}]")
print(f"缓存论文数: {stats['total_papers']}")
print(f"缓存大小: {stats['total_size_mb']:.2f} MB")

# 如果超过阈值，执行清理
if stats['total_size_mb'] > 4000:
    cache.cleanup(max_age_days=20)
    print("✓ 缓存已清理")
```

### 日志记录

```python
# 添加到主系统
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 在 PDF 处理时记录
logger.info(f"处理论文: {paper_id}")
logger.info(f"下载大小: {file_size} MB")
logger.info(f"缓存命中: {cache_hit}")
```

## 🔍 故障排除

### 问题 1: PyPDF2 导入失败
```bash
# 解决方案
pip install --upgrade PyPDF2
```

### 问题 2: 缓存目录权限
```bash
# 解决方案
chmod 755 ./cache/pdfs
```

### 问题 3: 下载超时
```python
# 增加超时时间
downloader = PDFDownloader(timeout=60)  # 60 秒
```

### 问题 4: LLM API 错误
```python
# 检查 API 密钥
import os
api_key = os.getenv("OPENAI_API_KEY")
assert api_key, "OPENAI_API_KEY 未设置"
```

### 问题 5: 内存不足
```python
# 减少并发数
processor = PDFProcessor(max_workers=2)  # 从 4 降低到 2
```

## 📈 性能优化

### 优化 1: 增加并发数
```python
# 对于高性能服务器
processor = PDFProcessor(max_workers=8)
```

### 优化 2: 增加缓存大小
```python
cache = CacheManager(
    cache_dir="/mnt/large_storage/pdfs",  # 使用更大的存储
)
```

### 优化 3: 使用 pdfplumber
```python
# pdfplumber 比 PyPDF2 更快
# 已在 requirements.txt 中包含
```

### 优化 4: 批量处理
```python
# 而不是逐个处理
enriched = adapter.enrich_papers_batch(papers)  # 推荐
# enriched = [adapter.enrich_paper_with_pdf(p) for p in papers]  # 不推荐
```

## 🔐 安全考虑

### 1. API 密钥
```bash
# 不要在代码中硬编码
# 使用环境变量
export OPENAI_API_KEY=sk-...
```

### 2. 文件权限
```bash
# 设置正确的权限
chmod 700 ./cache/pdfs
chmod 600 ./cache/pdfs/*.pdf
```

### 3. 输入验证
```python
# 验证 URL
from urllib.parse import urlparse

def validate_pdf_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and url.endswith('.pdf')
```

### 4. 错误日志
```python
# 不要暴露敏感信息
logger.error(f"下载失败: {url}")  # 可以
logger.error(f"API 密钥: {key}")   # 不能!
```

## 📋 部署检查清单

- [ ] 安装所有依赖
- [ ] 创建缓存目录
- [ ] 设置环境变量
- [ ] 配置 OpenAI API 密钥
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 手动测试几个论文
- [ ] 检查日志输出
- [ ] 验证缓存功能
- [ ] 测试清理功能
- [ ] 设置监控告警
- [ ] 文档化配置
- [ ] 准备备份方案

## 📞 技术支持

### 常见问题

**Q: 如何增加缓存大小?**
A: 修改清理策略:
```python
cache.cleanup(max_age_days=60, max_size_mb=10000)
```

**Q: 如何禁用 PDF 处理?**
A: 传递参数:
```python
enriched = adapter.enrich_papers_batch(papers, extract_pdf=False)
```

**Q: 如何使用本地 LLM?**
A: 实现自定义 LLM 客户端:
```python
class LocalLLM:
    def call(self, prompt):
        # 调用本地模型
        pass

adapter = PDFIntegrationAdapter(llm_client=LocalLLM())
```

**Q: 支持哪些 PDF 格式?**
A: 支持标准 PDF 1.4+ 格式。不支持:
- 扫描 PDF (需要 OCR)
- 加密 PDF
- 某些专有格式

## 📚 相关文档

- `PDF_USAGE_GUIDE.md` - 使用指南
- `PDF_IMPLEMENTATION.md` - 实现细节
- `PDF_FEATURES.md` - 功能说明
- `PDF_QUICKREF.md` - 快速参考

---

**部署指南版本**: 1.0  
**最后更新**: 2024  
**维护**: 开发团队
