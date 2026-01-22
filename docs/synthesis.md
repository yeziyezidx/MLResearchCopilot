首先，我将为您整理一下您的核心需求。

  需求整理 (Requirement Analysis)

  您的目标是将目前的单层总结模式，升级为以下三个层次、结构化、多维度的合成分析框架：

  层次一：子问题级别合成 (Sub-Query Synthesis)
   * 目标: 针对在研究过程中产生的每一个“子问题”（sub-query），对为其检索到的相关论文进行一次集中的、小范围的概括。
   * 输入:
       * sub_query_results: 每个子问题及其对应的原始论文检索结果。
       * structured_papers: 所有已经过解析、提取了详细元数据的论文。
   * 输出: 针对每个子问题，生成一段独立的摘要，阐述相关论文的核心发现。

  层次二：全局工作流/场景合成 (Global Workflow/Scenario Synthesis)
   * 目标: 从更高维度出发，结合用户的研究意图（问题、场景、工作流），将所有信息串联成一份具有全局视野的、连贯的总结。
   * 输入:
       * concepts: 描述用户意图的对象，包含problem, scenario, workflow, key_concepts。
       * problem (AcademicQuery): 包含research_background和academic_queris（即子问题列表）的对象。
       * structured_papers: 所有处理过的论文。
   * 过程与输出:
       1. 背景阐述: 首先，根据problem, scenario和research_background，生成一段研究背景介绍。
       2. 工作流合成: 按照用户定义的workflow，将“子问题级别合成”（层次一）的结论作为每个步骤的素材，最终融合成一段符合逻辑、条理清晰的工作流综述。

  层次三：横向对比分析 (Comparative Analysis)
   * 目标: 当研究任务涉及“对比”时，提供一个多维度、并排的详细比较。
   * 过程:
       1. 论文聚类: 首先，利用Embedding技术将所有论文按主题分成几个簇（Cluster）。
       2. 横向对比: 在每个簇内，针对性的抽取出每篇论文的objectives (目标), approaches (方法), contributions (贡献), models (模型)等关键信息，并以表格或结构化文本的形式进行横向对比分析。

  ---

  开发计划 (Development Plan)

  基于以上需求，我制定了如下的开发计划：

  第一阶段：重构 `synthesis` 模块

   1. 重构 `src/synthesis/summarizer.py`:
       * 将Summarizer类作为新的合成流程的总入口。
       * 我会重构当前的synthesize方法，使其成为一个“调度中心”，负责调用新逻辑来完成上述三个层次的合成任务。
       * 在Summarizer内部，我将创建三个新的私有方法，分别对应三个合成层次：
           * _synthesize_sub_queries(...): 实现“子问题级别合成”。
           * _synthesize_global_workflow(...): 实现“全局工作流合成”。
           * _synthesize_comparative_analysis(...): 实现“横向对比分析”。

   2. 增强 `src/synthesis/aggregator.py`:
       * 现有的cluster_papers方法将用于“横向对比分析”的聚类步骤。
       * 我会考虑增强现有的aggregate_*方法，或者添加新方法，以便更方便地提取用于横向对比的字段（例如，按论文ID聚合它们的贡献）。

  第二阶段：实现新的三层合成逻辑

   1. 实现 `_synthesize_sub_queries`: 该方法会遍历所有子问题，找到每个子问题对应的论文，并调用大语言模型（LLM）为每组论文生成小结。
   2. 实现 `_synthesize_global_workflow`: 该方法将构建一个包含研究背景、场景、工作流和第一阶段产出的“子问题摘要”的复杂提示（Prompt），然后让LLM生成一份高度概括、逻辑连贯的全局综述。
   3. 实现 `_synthesize_comparative_analysis`: 该方法会先调用aggregator.cluster_papers进行聚类。然后，在每个聚类内部，提取关键信息并格式化，最后调用LLM生成结构化的对比分析报告（例如，Markdown表格）。

  第三阶段：更新 `main.py` 的调用逻辑

   1. 修改 `ResearchEngine.process_query()`:
       * 在第7步“cross-paper synthesis”中，我会用一个对新的summarizer.synthesize方法的调用，替换掉目前分散的调用。
       * 在调用时，我会将所有需要的数据（query, concepts, problem, sub_query_results, structured_papers）作为参数传入。
       * 新的合成结果将是一个包含所有三个层次分析的、结构化的字典，我会将其完整地存入最终结果中。
