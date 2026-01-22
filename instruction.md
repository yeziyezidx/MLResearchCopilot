用户问题  
   ↓  
Research 意图理解 + 领域问题构建[by LLM]
   ↓  
What: Broad Answer 关键概念理解[by LLM + 联网搜]
   ↓  
Which: Approach抽取（例如：模型名称、论文名、关键库、方法术语） [by LLM]
   P1. Answer-Oriented System Framing
   P2. Workflow-level Research Question Decomposition
   P3. Problem–Technique Alignment
   P4. Academic Query Generation
   ↓  
|-->语义检索（Semantic Search）[by Domain Specific Retrieval Model: github, huggingface, 论文库（arXiv、ACL Anthology）]
|   ↓  
|候选论文 (Top-K)
|   ↓  
|---Related Work 理解
   ↓  
LLM 抽取结构化信息（标题、摘要、方法、结果、贡献…）
   ↓  
模型并行运行，对每篇论文生成结构化行
   ↓  
表格化（Spreadsheet UI）
   ↓  
跨论文聚合与证据综合（LLM 多文档 summarization）
   ↓  
引用溯源（sentence-level citation ）