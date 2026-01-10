"""
intent_understanding module - Analyze user queries to understand research intent
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from string import Template
TEMPLATE = Template(r'''
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
class BroadAnswer:
    """Broad answer structure"""
    summary: str
    problem: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "summary": self.summary,
            "problem": self.problem,
        }   

class BroadAnswerGenerator:
    """Broad answer generation module"""
    
    def __init__(self, llm_client=None):
        """
        Initialize broad answer generation component
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def generate(self, query: str, context: Optional[str] = None) -> str:
        """
        Generate a broad answer to the user's query
        
        Args:
            query: User's question
            context: Background information (optional)
            
        Returns:
            BroadAnswer: Broad answer object
        """
        # build prompt
        prompt = self._build_prompt(query, context)
        
        # call LLM
        if self.llm_client:
            response = self.llm_client.call(prompt, max_tokens=10240, output_format="text")
            answer = self._parse_response(response)
        else:
            # local simple processing
            answer = self._local_understanding(query)

        return answer
    
    def _build_prompt(self, query: str, context: Optional[str] = None) -> str:
        """Build prompt using template"""
        # Load the intent_analysis template
        prompt  = TEMPLATE.substitute(query=query, context=context if context else "")
        
        return prompt

    def _parse_response(self, response: str) -> BroadAnswer:
        """Parse LLM response to extract intent data"""
        try:
            # Extract JSON part from the response
            start_tag = "<answer>"
            end_tag = "</answer>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            answer = response[start_idx:end_idx].strip()
            
            start_tag = "<problem>"
            end_tag = "</problem>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            problem = response[start_idx:end_idx].strip()         
            return BroadAnswer(summary=answer, problem=problem)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing intent understanding response: {e}")
            return {}
    
    def _local_understanding(self, query: str) -> Dict:
        """local simple processing"""
        # This is a very naive implementation for demonstration purposes
        return BroadAnswer(summary=f"Broad answer for query: {query}")
