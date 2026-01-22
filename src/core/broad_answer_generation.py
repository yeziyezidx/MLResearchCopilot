"""
Broad answer generation module - Generate comprehensive, up-to-date answers using LLM + web search
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from string import Template
from .web_search import get_searcher, SearchResult

LLM_ANSWER_TEMPLATE = Template(r'''
You are an academic research assistant responsible for **accurately understanding and answering the user’s research question**.
Based strictly on the provided query and background context, *answer the question and extract the academic research problem(means you should ignore the dirtywork)s*.

### Output Requirements (must be strictly followed)

* Concise content and clear structure
* No emotional language or unnecessary rhetoric

### Output Format (fixed)

```
<response>
  <answer>your answer</answer>
  <problem>structured research problem if any</problem>
</response>
```

### User Input

* Query: $query
* Background Context: $context

''')
broad_answer_synthesis_template = Template(r'''
You are an expert research assistant tasked with synthesizing current information from web search results with your knowledge base to provide a comprehensive, accurate, and up-to-date broad answer to research questions.
Based on the following recent web search results and your knowledge, provide a comprehensive answer to the research question.\n\n
Query: $query\n\n
Recent Web Search Results:\n
$search_results\n\n
Please synthesize this information to:\n
1. Provide a current, comprehensive answer\n
2. Highlight key concepts and recent developments\n
3. Identify authoritative sources mentioned\n
4. Note any emerging trends or recent changes\n\n
 Output Format:
<response>
<answer>Comprehensive answer synthesizing web results and knowledge</answer>\n  
<key_concepts>List of key concepts and definitions</key_concepts>\n  
<recent_developments>Any recent trends, developments, or changes mentioned</recent_developments>
<authoritative_sources>Key sources and authorities mentioned</authoritative_sources>\n
 </ response>\n                                
''')
search_result_template = Template(r'''
- Title:$title\n  
URL: $url\n  
Summary: $snippet\n
''')


@dataclass
class BroadAnswer:
    """Broad answer structure with web search integration"""
    summary: str
    problem: Optional[str] = None
    key_concepts: Optional[List[str]] = None
    recent_developments: Optional[List[str]] = None
    authoritative_sources: Optional[List[str]] = None
    search_results: Optional[List[SearchResult]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "summary": self.summary,
            "problem": self.problem,
            "key_concepts": self.key_concepts or [],
            "recent_developments": self.recent_developments or [],
            "authoritative_sources": self.authoritative_sources or [],
            "search_results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source
                }
                for r in (self.search_results or [])
            ],
        }   

class BroadAnswerGenerator:
    """Broad answer generation module with web search + LLM synthesis"""
    
    def __init__(self, llm_client=None, enable_web_search: bool = True, num_search_results: int = 5):
        """
        Initialize broad answer generation component
        
        Args:
            llm_client: LLM client instance
            enable_web_search: Whether to search the web for current information (default: True)
            num_search_results: Number of web search results to collect and synthesize
        """
        self.llm_client = llm_client
        self.enable_web_search = enable_web_search
        self.num_search_results = num_search_results
        self.searcher = get_searcher(prefer_engine = "speedbird") if enable_web_search else None
    
    def generate(self, query: str, context: Optional[str] = None) -> BroadAnswer:
        """
        Generate a broad answer to the user's query, optionally enhanced with web search.
        
        Args:
            query: User's question
            context: Background information (optional)
            
        Returns:
            BroadAnswer: Broad answer object with summary, concepts, and sources
        """
        # Step 1: Optionally search the web for recent information
        search_results = []
        if self.enable_web_search and self.searcher:
            print(f"Searching web for: {query}")
            search_results = self.searcher.search(query, self.num_search_results)
            print(f"Found {len(search_results)} search results")
        
        # Step 2: Build prompt (using template or fallback)
        if self.enable_web_search and search_results:
            prompt = self._build_prompt_with_search(query, context, search_results)
        else:
            prompt = self._build_prompt(query, context)
        
        # Step 3: Call LLM to synthesize
        if self.llm_client:
            response = self.llm_client.call(prompt, max_tokens=10240, output_format="text")
            answer = self._parse_response(response)
            answer.search_results = search_results
        else:
            # Fallback: local simple processing
            answer = self._local_understanding(query)
        
        return answer
    
    def _build_prompt(self, query: str, context: Optional[str] = None) -> str:
        """Build prompt using template (legacy, LLM-only)"""
        # Load the intent_analysis template
        prompt  = LLM_ANSWER_TEMPLATE.substitute(query=query, context=context if context else "")
        
        return prompt
    
    def _build_prompt_with_search(self, query: str, context: Optional[str] = None, search_results: List[SearchResult] = None) -> str:
        """Build prompt with web search results for LLM synthesis"""
        try:
            result_template = search_result_template
            
            # Format search results
            formatted_results = ""
            if search_results:
                for i, result in enumerate(search_results, 1):
                    formatted_results += result_template.substitute(
                        title=result.title,
                        url=result.url,
                        snippet=result.snippet
                    )
            
            # Get the synthesis prompt
            synthesis_prompt = broad_answer_synthesis_template
            prompt = synthesis_prompt.substitute(
                query=query,
                search_results=formatted_results if formatted_results else "No search results available"
            )
        except Exception as e:
            print(f"Warning: Could not load template for web search synthesis: {e}")
            # Fallback: construct a manual prompt
            formatted_results = ""
            if search_results:
                for i, result in enumerate(search_results, 1):
                    formatted_results += f"{i}. {result.title}\n   URL: {result.url}\n   {result.snippet}\n\n"
            
            prompt = f"""You are an expert research assistant. Based on the following recent web search results and your knowledge, provide a comprehensive answer to the research question.

Query: {query}

Recent Web Search Results:
{formatted_results}

Please synthesize this information to:
1. Provide a current, comprehensive answer
2. Highlight key concepts and recent developments
3. Identify authoritative sources mentioned
4. Note any emerging trends or changes

Output Format:
<response>
  <answer>Comprehensive answer synthesizing web results and knowledge</answer>
  <key_concepts>Key concepts list</key_concepts>
  <recent_developments>Recent developments list</recent_developments>
  <authoritative_sources>Source list</authoritative_sources>
</response>
"""
        
        return prompt

    def _parse_response(self, response: str) -> BroadAnswer:
        """Parse LLM response to extract broad answer data"""
        try:
            # Extract answer
            start_tag = "<answer>"
            end_tag = "</answer>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            answer = response[start_idx:end_idx].strip()
            
            # Extract problem (if exists)
            problem = None
            try:
                start_tag = "<problem>"
                end_tag = "</problem>"
                start_idx = response.index(start_tag) + len(start_tag)
                end_idx = response.index(end_tag)
                problem = response[start_idx:end_idx].strip()
            except ValueError:
                pass
            
            # Extract key concepts
            key_concepts = []
            try:
                start_tag = "<key_concepts>"
                end_tag = "</key_concepts>"
                start_idx = response.index(start_tag) + len(start_tag)
                end_idx = response.index(end_tag)
                concepts_text = response[start_idx:end_idx].strip()
                key_concepts = [c.strip() for c in concepts_text.split("\n") if c.strip()]
            except ValueError:
                pass
            
            # Extract recent developments
            recent_developments = []
            try:
                start_tag = "<recent_developments>"
                end_tag = "</recent_developments>"
                start_idx = response.index(start_tag) + len(start_tag)
                end_idx = response.index(end_tag)
                devs_text = response[start_idx:end_idx].strip()
                recent_developments = [d.strip() for d in devs_text.split("\n") if d.strip()]
            except ValueError:
                pass
            
            # Extract authoritative sources
            sources = []
            try:
                start_tag = "<authoritative_sources>"
                end_tag = "</authoritative_sources>"
                start_idx = response.index(start_tag) + len(start_tag)
                end_idx = response.index(end_tag)
                sources_text = response[start_idx:end_idx].strip()
                sources = [s.strip() for s in sources_text.split("\n") if s.strip()]
            except ValueError:
                pass
            
            return BroadAnswer(
                summary=answer,
                problem=problem,
                key_concepts=key_concepts or None,
                recent_developments=recent_developments or None,
                authoritative_sources=sources or None
            )
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing broad answer response: {e}")
            # Return at least the raw response as summary
            return BroadAnswer(summary=response)
    
    def _local_understanding(self, query: str) -> BroadAnswer:
        """Local simple processing (fallback when LLM not available)"""
        return BroadAnswer(summary=f"Broad answer for query: {query}")
