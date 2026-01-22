"""
Multi-document comprehensive summarization module
"""
from typing import List, Dict

from src.core.concept_understanding import ConceptDefinition
from src.pdf_management.parser import ExtractedInfo
from src.synthesis.aggregator import Aggregator
from src.slm.slm_client import SLMClient
from src.core.concept_understanding import AcademicQuery
from string import Template
import json

query_paper_synthesis_template = Template(r'''
You are an expert research assistant tasked with synthesizing paper comparsing results and generting a research review.
**Primary Research Goal:** $query
**Identified Workflow:** $workflow
**Research Background:** $problem

**Analysis of Sub-Topics:** 
(Summaries of sub-topic analyses would be formatted and inserted here)
$subquery_comparisons
**Task:** Based on all the provided context and detailed analyses, write a final, high-level executive summary that follows the specified workflow and addresses the user's primary goal.
Output Format:
<response>
<answer>your answer</answer>
</response>
''')

subquery_paper_synthesis_template = Template(r'''
You are an expert research assistant tasked with synthesizing paper comparsing results and generting a research review.
**Primary Research Goal:** $query

**Analysis of  papers:** 
(Summaries of research paper analyses would be formatted and inserted here)
$paper_comparisons
**Task:** Based on all the provided context and detailed analyses, write a final, high-level executive summary that follows the specified workflow and addresses the user's primary goal.
Output Format:
<response>
<answer>your answer</answer>
</response>
''')

class Summarizer:
    """
    Multi-document comprehensive summarizer that orchestrates a
    multi-layered synthesis process.
    """

    def __init__(self, llm_client=None, slm_client: SLMClient = None, aggregator: Aggregator = None):
        """
        Initializes the summarizer.
        
        Args:
            llm_client: Client for large language models (text generation).
            slm_client: Client for smaller language models (e.g., embeddings).
            aggregator: Aggregator instance for clustering and data extraction.
        """
        self.llm_client = llm_client
        self.slm_client = slm_client
        self.aggregator = aggregator or Aggregator(llm_client=llm_client)

    def synthesize(
        self,
        query: str,
        concepts: ConceptDefinition,
        problem: AcademicQuery,
        sub_query_results: Dict[str, List[Dict]],
        structured_papers: List[ExtractedInfo]
    ) -> Dict:
        """
        Orchestrates the multi-layered synthesis process.
        """
        if not structured_papers:
            return {
                "sub_query_synthesis": {},
                "global_synthesis": {},
                "error": "No structured papers provided for synthesis.",
            }

        # Layer 1: Generate a detailed comparative analysis for each sub-query
        sub_query_synthesis = self._synthesize_sub_queries(
            sub_query_results, structured_papers
        )

        # Layer 2: Generate a global synthesis, including a global comparative
        # analysis and a final executive summary.
        global_synthesis = self._synthesize_global_workflow(
            query, concepts, problem, sub_query_synthesis
        )

        return {
            "sub_query_synthesis": sub_query_synthesis,
            "global_synthesis": global_synthesis,
        }

    def _synthesize_comparative_analysis(
        self, query: str, papers_to_analyze: List[ExtractedInfo]
    ) -> Dict:
        """
        Core analysis engine: Takes a list of papers and returns a detailed
        comparative analysis report on them.
        """
        print(f"  [Core Analysis] Performing comparative analysis on {len(papers_to_analyze)} papers...")
        if not papers_to_analyze:
            return {"error": "No papers provided to analyze."}

        comparison_data = self.aggregator.get_comparison_data(papers_to_analyze)
        comparison_data = "<paper>" + "</paper><paper>".join([json.dumps(item) for item in comparison_data]) + "</paper>"
        
        prompt = subquery_paper_synthesis_template.substitute(query=query, paper_comparisons=comparison_data)  
            
        
        if self.llm_client:
            response = self.llm_client.call(prompt, max_tokens=10240, output_format="text")
            answer = self._parse_response(response)
        else:
            # Fallback: local simple processing
            answer = prompt  

        return answer

    def _synthesize_sub_queries(
        self,
        sub_query_results: Dict[str, List[Dict]],
        all_structured_papers: List[ExtractedInfo],
    ) -> Dict:
        """
        Generates a comparative analysis report for each sub-query (Layer 1).
        """
        print(" -> Layer 1: Generating comparative analysis for each sub-query...")
        all_sub_query_analyses = {}
        paper_map_by_url = {paper.url: paper for paper in all_structured_papers}

        for sub_query, raw_results in sub_query_results.items():
            # Find the structured papers that match the raw results for this sub-query
            papers_for_sub_query = []
            for raw_paper in raw_results:
                if raw_paper.get('pdf_url') in paper_map_by_url:
                    papers_for_sub_query.append(paper_map_by_url[raw_paper['pdf_url']])
            
            if papers_for_sub_query:
                # Generate a full comparative analysis for this subset of papers
                analysis_report = self._synthesize_comparative_analysis(sub_query, papers_for_sub_query)
                all_sub_query_analyses[sub_query] = analysis_report
            else:
                all_sub_query_analyses[sub_query] = {"message": "No processed papers found for this sub-query."}
            
        return all_sub_query_analyses

    def _synthesize_global_workflow(
        self,
        query: str,
        concepts: ConceptDefinition,
        problem: AcademicQuery,
        sub_query_synthesis: Dict,
    ) -> Dict:
        """
        Generates a global synthesis, including a global comparative analysis
        and a final executive summary (Layer 2).
        """
        print(" -> Layer 2: Generating global synthesis...")

            
        # Placeholder for building a sophisticated prompt
        sub_query_reports = "<sub_query_report>" + "</sub_query_report><sub_query_report>".join([
            f"<sub_query_report><sub_query>{sub_query}</sub_query><analysis>{analysis}</analysis></sub_query_report>"
            for sub_query, analysis in sub_query_synthesis.items()
        ]) + "</sub_query_report>"
        prompt = query_paper_synthesis_template.substitute(query = query, workflow=concepts.workflow, problem=problem.research_background, subquery_comparisons=sub_query_reports)
        
        # executive_summary = self.llm_client.text_completion(prompt) # Placeholder for actual call
        if self.llm_client:
            response = self.llm_client.call(prompt, max_tokens=10240, output_format="text")
            answer = self._parse_response(response)
        else:
            # Fallback: local simple processing
            answer = prompt  
        return answer
    def _parse_response(self, response: str) -> Dict:
        """Parses LLM response"""

        # Extract answer
        start_tag = "<answer>"
        end_tag = "</answer>"
        start_idx = response.index(start_tag) + len(start_tag)
        end_idx = response.index(end_tag)
        answer = response[start_idx:end_idx].strip()
        return {
            "executive_summary": answer
        }