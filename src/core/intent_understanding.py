"""
intent_understanding module - Analyze user queries to understand research intent
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from string import Template
TEMPLATE = Template(r'''
You are an expert research assistant specializing in understanding and analyzing academic research queries. Your task is to perform *scholarly-level interpretation* of the user’s research question and extract research intent using academically rigorous terminology.
## RESPONSE FORMAT (STRICT)
You MUST output using these tags for easy parsing:

<response>

  <analysis>
    Step-by-step scholarly reasoning:
    1. Interpret the user’s research question in depth.
    2. Identify the precise academic subfields involved (avoid vague, broad domains).
    3. Determine the research intent type using established research-methodology terminology , must include the specific query + scenario
       (e.g., "comparative evaluation of evidence extraction in AI search systems" rather than simply "method comparison of information extraction method").
    4. Analyze and refine the original question into specific, operationalized, academically valid research questions.
       - Use terminology from information extraction, retrieval-augmented generation,
         document understanding, and web data mining.
    5. Explain how each refined question corresponds to known research tasks 
       (e.g., “evidence extraction”, “passage ranking”, “content consolidation”).
  </analysis>

  <json>
    {
      "intent_type": {
        "zh": "",
        "en": ""
      },
      "research_area": {
        "zh": "",
        "en": ""
      },
      "key_topics": {
        "zh": [],
        "en": []
      },
      "research_questions": {
        "zh": [],
        "en": []
      }
    }
  </json>

  <methodologies>
    Provide concrete academic methodologies corresponding to the refined research questions.
    Use precise terminology such as:
    - Evidence extraction in RAG systems
    - Dense retrieval in open-domain QA 
    - multi-stage pretrain of vision-language models
    - data synthesis for deep research systems
  </methodologies>

</response>

## USER QUESTION
Queyr: $query
BackGround Context: $context
''')
@dataclass
class ResearchIntent:
    """Research intent structure"""
    original_query: str
    intent_type: str  # e.g., "literature_review", "method_comparison", "problem_solving"
    research_area: str
    key_topics: List[str]
    research_questions: List[str]
    context: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        intent_dict = {"original_query": self.original_query}
        if isinstance(self.intent_type, dict):
            intent_dict["intent_type"] = list(self.intent_type.values())
        else:
            intent_dict["intent_type"] = self.intent_type
        if isinstance(self.research_area, dict):
            intent_dict["research_area"] = list(self.research_area.values())
        else:
            intent_dict["research_area"] = self.research_area
        if isinstance(self.key_topics, dict):
            intent_dict["key_topics"] = list(self.key_topics.values())
        else:
            intent_dict["key_topics"] = self.key_topics
        if isinstance(self.research_questions, dict):
            intent_dict["research_questions"] = list(self.research_questions.values())
        else:
            intent_dict["research_questions"] = self.research_questions
        return intent_dict


class IntentUnderstanding:
    """Intent understanding module"""
    
    def __init__(self, llm_client=None):
        """
        Initialize intent understanding component
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def understand(self, query: str, context: Optional[str] = None) -> ResearchIntent:
        """
        Understand user's research intent
        
        Args:
            query: User's question
            context: Background information (optional)
            
        Returns:
            ResearchIntent: Research intent object
        """
        # build prompt
        prompt = self._build_prompt(query, context)
        
        # call LLM
        if self.llm_client:
            response = self.llm_client.call(prompt, output_format="json")
            intent_data = self._parse_response(response)
        else:
            # local simple processing
            intent_data = self._local_understanding(query)

        return ResearchIntent(
            original_query=query,
            intent_type=intent_data.get("intent_type", ["literature_review"]),
            research_area=intent_data.get("research_area", []),
            key_topics=intent_data.get("key_topics", []),
            research_questions=intent_data.get("research_questions", []),
            context=context,
        )
    
    def _build_prompt(self, query: str, context: Optional[str] = None) -> str:
        """Build prompt using template"""
        # Load the intent_analysis template
        prompt  = TEMPLATE.substitute(query=query, context=context if context else "")
        
        return prompt

    def _parse_response(self, response: str) -> Dict:
        """Parse LLM response to extract intent data"""
        try:
            # Extract JSON part from the response
            start_tag = "<json>"
            end_tag = "</json>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            json_str = response[start_idx:end_idx].strip()
            
            intent_data = json.loads(json_str)

            for key, value in intent_data.items():
                if isinstance(value, dict):
                    result = []
                    for v in value.values():
                        if isinstance(v, list):
                            result.extend(v)
                        elif isinstance(v, str):
                            result.append(v)
                    intent_data[key] = result
            return intent_data
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing intent understanding response: {e}")
            return {}
    
    def _local_understanding(self, query: str) -> Dict:
        """local simple processing"""
        # This is a very naive implementation for demonstration purposes
        return {
            "intent_type": {'zh': '针对联网AI搜索系统的后检索阶段证据抽取与答案生成过程的过程导向分析', 'en': 'Process-oriented analysis of post-retrieval evidence extraction and answer synthesis in AI-connected search systems'},
            "research_area":  {'zh': '信息抽取、文档理解、检索增强生成、开放域问答', 'en': 'Information Extraction, Document Understanding, Retrieval-Augmented Generation, Open-Domain Question Answering'},
            "key_topics": query.split(),
            "research_questions":  {'zh': ['检索增强生成系统在开放域问答中，如何从已检索网页中进行证据抽取？', 'AI搜索系统如何对单网页中的多个证据片段进行排序、过滤与整合，以确保答案的相关性与准确性？', '文档结构分析与语义分段在提升HTML网页信息抽取质量中起到何种作用？', '在深度研究流程中，如何解决多文档答案合成过程中的冲突与冗余信息？'], 'en': ['What algorithms and models are employed in retrieval-augmented generation systems to perform evidence extraction from retrieved web pages in open-domain question answering tasks?', 'How do AI search systems rank, filter, and consolidate multiple evidence passages from a single webpage to ensure relevance and factual accuracy in generated answers?', 'What role do document structure analysis and semantic segmentation play in improving information extraction quality from HTML-based web resources?', 'How are conflicting or redundant information instances resolved during multi-document content synthesis in deep research pipelines?']},
        }
