"""
Concept UnderStanding Module: Understand the Broad Answers
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests
from .broad_answer_generation import BroadAnswer
from string import Template
import json

concept_understanding_template = Template(r'''

You are a senior research scientist and systems architect. 
Your job is to read the provided domain materials and behave like a rigorous researcher:

Goals:
1) Rapidly internalize the provided domain inputs (summaries, concepts, developments, notes).
2) Infer the user's true problem behind the surface query.
3) Identify the most plausible application scenario (e.g., RAG system, search & recommendation, ad ranking, content moderation, knowledge extraction, data engineering, analytics, etc.).
4) Reconstruct the canonical workflow/pipeline for that scenario (e.g. for search-reco: query understanding → recall → re-ranking → layout/cardization → filling → reflow → QA).
5) Pinpoint which module(s) in the workflow the user's question likely belongs to, and explain why.
6) Extract the related concepts in workflow without redundant

Principles:
- Use English
- Prefer concrete terminology used in industry (module names, API boundaries, data artifacts).
- Always state assumptions if information is missing; separate assumptions from evidence.
- Include counterfactual checks: if an alternative scenario could also explain the question, list it with probability.
- When mapping to workflow, name inputs/outputs and typical signals/features for that module.
- NEVER reveal hidden reasoning or internal deliberations; output final structured results only.
### Input   
Original Query: $query
Knowledge from webpage: $knowledge
                                          
### Output Requirements (must be strictly followed)
<response>
  <scenario> application scenario  </scenario> 
  <workflow>system workflow</workflow>
  <problem>user's true problem </problem>
  <key_concepts> related concepts </problem>
</response>
                  
''')

paper_search_template = Template(r'''

You are an expert research assistant specialized in academic knowledge retrieval.

Your task:
1. Read the provided context: original query, problem statement, scenario, workflow, and related key concepts.
2. Use your own domain knowledge + provided context to:
   a) Formulate a **structured research question** that captures the essence of the problem in an academic tone.
   b) Generate **3–5 ultra-concise academic search queries**, each ≤7 tokens, highly relevant to the problem and scenario, seperate by ";"
   c) Suggest **relevant academic paper domains** (e.g., arxiv.org, acm.org, ieee.org, springer.com) where such queries would yield authoritative results, seperate by ";"

### Input  
Original Query: $query
Knowledge from webpage: $knowledge
                                 
### Output Requirements (must be strictly followed)
<response>
  <research_question> structured research question  </research_question> 
  <academic_query>academic search query</academic_query>
  <relevant_domains>relevant academic paper domains </relevant_domains>
</response>
                  
''')

@dataclass
class ConceptDefinition:
    """definition"""
    problem: str
    scenario: str
    workflow: str
    related_concepts: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "problem": self.problem,
            "scenario": self.scenario,
            "workflow": self.workflow,
            "key_concepts": self.related_concepts or [],
        }   
@dataclass
class AcademicQuery:
    """definition"""
    research_background: str
    academic_queris: List[str]
    relevant_domains: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "research_background": self.research_background,
            "academic_queris": self.academic_queris or [],
            "relevant_domains": self.relevant_domains or [],
        } 
class ConceptUnderstanding:
    """Concept UnderStanding Module"""
    
    def __init__(self, llm_client=None):
        """initialize"""
        self.llm_client = llm_client
        self.definitions_cache: Dict[str, ConceptDefinition] = {}
    
    def understand_concepts(self, query, broadanswers: List[BroadAnswer]) -> ConceptDefinition:
        """
        given the query and the broad answers,
        Abstract the implicit end-to-end system or process that must be understood to produce such an answer
        Infer what kind of answer structure the user is actually seeking
        
        Args:
            query, broadanswers
            
        Returns:
            Dict: 
        """

        knowledge = "<knowldge>"
        for answer in broadanswers:
            knowledge += "<summary>" + answer.summary + "</summary"
            knowledge += "<key_concepts>" + "###".join([concept[:32] for concept in answer.key_concepts]) if answer.key_concepts else "" + "</key_concepts>"
        knowledge += "</knowldge>"

        prompt = concept_understanding_template.substitute(query=query, knowledge=knowledge)

        # call LLM
        if self.llm_client:
            response = self.llm_client.call(prompt, max_tokens=10240 , temperature=0.3 ,output_format="json")
            concept = self._parse_response(response)
        else:
            concept = self._local_understanding(query)
        
        return concept
    
    def generate_paper_search_query(self, query, concept: ConceptDefinition) -> AcademicQuery:
        """
        given the query and the concepts,
        generate the query for paper search
        
        Args:
            query, concept
            
        Returns:
            Dict: 
        """


        prompt = paper_search_template.substitute(query=query, knowledge=json.dumps(concept.to_dict()))

        # call LLM
        if self.llm_client:
            response = self.llm_client.call(prompt, max_tokens=10240,output_format="json")
        else:
            response = ""
        
        research_background = None

        try:
            start_tag = "<research_question>"
            end_tag = "</research_question>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            research_background = response[start_idx:end_idx].strip()
        except ValueError:
            pass
                    # Extract key concepts
        academic_query = []
        try:
            start_tag = "<academic_query>"
            end_tag = "</academic_query>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            concepts_text = response[start_idx:end_idx].strip()
            academic_query = [c.strip() for c in concepts_text.split(";") if c.strip()]
        except ValueError:
            pass
        
        relevant_domains = []
        try:
            start_tag = "<relevant_domains>"
            end_tag = "</relevant_domains>"
            start_idx = response.index(start_tag) + len(start_tag)
            end_idx = response.index(end_tag)
            concepts_text = response[start_idx:end_idx].strip()
            relevant_domains = [c.strip() for c in concepts_text.split(";") if c.strip()]
        except ValueError:
            pass
        
        return AcademicQuery(
            research_background = research_background,
            academic_queris = academic_query,
            relevant_domains = relevant_domains
        )
    
    def _parse_response(self, response: str) -> BroadAnswer:
        """Parse LLM response to extract broad answer data"""
        try:

            
            # Extract scenario (if exists)
            scenario = None
            try:
                start_tag = "<scenario>"
                end_tag = "</scenario>"
                start_idx = response.index(start_tag) + len(start_tag)
                end_idx = response.index(end_tag)
                scenario = response[start_idx:end_idx].strip()
            except ValueError:
                pass
            
            # Extract workflow
            workflow = None
            try:
                start_tag = "<workflow>"
                end_tag = "</workflow>"
                start_idx = response.index(start_tag) + len(start_tag)
                end_idx = response.index(end_tag)
                workflow = response[start_idx:end_idx].strip()
            except ValueError:
                pass
            
            # Extract problem
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
            
            return ConceptDefinition(
                problem=problem,
                scenario=scenario,
                workflow=workflow,
                related_concepts=key_concepts
            )
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing broad answer response: {e}")
            # Return at least the raw response as summary
            return ConceptDefinition(problem=response)
    
    def _local_understanding(self, query: str) -> ConceptDefinition:
        """Local simple processing (fallback when LLM not available)"""
        return ConceptDefinition(problem=f"Broad answer for query: {query}")