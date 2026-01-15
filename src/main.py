"""
Entrance - ML Research Copilot
"""
import sys
import os
from pathlib import Path

# add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_config
from src.llm.client import LLMClient
from src.core.intent_understanding import IntentUnderstanding
from src.core.broad_answer_generation import BroadAnswerGenerator
from src.core.concept_understanding import ConceptUnderstanding
from src.core.problem_formulation import ProblemFormulator
from src.retrieval.retriever import Retriever
from src.extraction.paper_extractor import PaperExtractor
from src.synthesis.aggregator import Aggregator
from src.synthesis.summarizer import Summarizer


class ResearchEngine:
    """Research Engine for ML Research Copilot"""
    
    def __init__(self, config=None, enable_debug: bool = True):
        """Initialize the research engine"""
        self.config = config or get_config()
        self.llm_client = None
        self.queries = {} 
        
        # initial LLM client
        self.llm_client = LLMClient(
            provider=self.config.PROVIDER,
            api_key=self.config.OPENAI_API_KEY,
            model=self.config.MODEL_NAME,
            base_url=self.config.BASE_URL_OR_ENDPOINT,
            papyrus_quota_id=self.config.PAPYRUS_QUOTA_ID,
            papyrus_timeout_ms=self.config.PAPYRUS_TIMEOUT_MS,
            papyrus_verify_scope=self.config.PAPYRUS_VERIFY_SCOPE,
        )
        
        # initialize modules
        self.intent_analyzer = IntentUnderstanding(self.llm_client)
        self.broad_answer_generator = BroadAnswerGenerator(self.llm_client, enable_web_search=True, num_search_results=5)
        self.concept_understander = ConceptUnderstanding(self.llm_client)
        self.problem_formulator = ProblemFormulator(self.llm_client)
        self.retriever = Retriever()
        self.paper_extractor = PaperExtractor(self.llm_client)
        self.aggregator = Aggregator()
        self.summarizer = Summarizer(self.llm_client)

        # debug logger
        if enable_debug:
            from tests.debugger import DebugLogger
            self.debug_logger = DebugLogger()
        else:
            self.debug_logger = None
    
    def process_query(self, query: str, context: str = None) -> str:
        """
        process a user query
        
        Args:
            query
            context
            
        Returns:
            str: query_id
        """
        import uuid
        query_id = str(uuid.uuid4())
        
        print(f"\n{'='*60}")
        print(f"processing {query_id}")
        print(f"query: {query}")
        print(f"{'='*60}\n")
        
        try:
            # 1. intent understanding
            print("\n-- step 1: understanding intent")
            intent = self.intent_analyzer.understand(query, context)
            print(f" -> user intent: {intent.intent_type}")
            print(f" -> research area: {intent.research_area}")
            print(f" -> research questions: {intent.research_questions}")
            if self.debug_logger:
                self.debug_logger.log_step("intent_understanding", intent, step_number=1)
            
            # 2. Broad answer Generation
            print("\n-- step 2: Broad answer / concept understanding...")
            broad_answers = []
            for idx, rewrite_query in enumerate(intent.research_questions):
                print(f" -> rewriting query: {rewrite_query}")
                answer = self.broad_answer_generator.generate(rewrite_query, query)
                print(f" -> generated broad answer: {answer.summary[:100]}...")
                broad_answers.append(answer)
                if self.debug_logger:
                    self.debug_logger.log_step(f"broad_answer_{idx}", answer, step_number=2)
            
            # 3. Get scenario concepts
            print("\n-- step 3: Get scenario concepts...")
            concepts = self.concept_understander.understand_concepts(query, broad_answers)
            print(f" -> related queries: {concepts.related_concepts}")
            if self.debug_logger:
                self.debug_logger.log_step("get_scenario_concepts", concepts , step_number=3)
            
            # 4. problem formulation
            print("\n-- step 4: acamedic problem formulation...")
            problem = self.concept_understander.generate_paper_search_query(query, concepts)
            print(f" -> academic queries: {problem.academic_queris}")
            print(f" -> academic domains: {problem.relevant_domains}")
            if self.debug_logger:
                self.debug_logger.log_step("generate_academic_queries", problem , step_number=4)

            # 5. paper retrieval
            print("\n-- step 5: paper retrieval...")
            papers = self.retriever.search_by_keywords(concepts, top_k=self.config.SEARCH_TOP_K)
            print(f" -> retrieved {len(papers)} papers")
            
            # 6. information extraction
            print("\n-- step 6: information extraction...")
            structured_papers = []
            for paper in papers:
                structured = self.paper_extractor.extract(paper.to_dict())
                structured_papers.append(structured)
            print(f" -> processed {len(structured_papers)} papers")
            
            # 7. cross-paper synthesis
            print("\n-- step 7: cross-paper synthesis...")
            synthesis = self.summarizer.synthesize(structured_papers)
            aggregation = self.aggregator.generate_summary(structured_papers)
            print(f" -> identified {aggregation['total_papers']} papers")
            print(f" -> top methods: {list(aggregation['top_methods'].keys())[:3]}")
            
            # save results
            self.queries[query_id] = {
                "query": query,
                "context": context,
                "intent": intent.to_dict(),
                "concepts": concepts.to_dict(),
                "problem": problem.to_dict(),
                "papers": [p.to_dict() for p in structured_papers],
                "synthesis": synthesis,
                "aggregation": aggregation,
                "status": "completed",
            }
            
            print(f"\n✅ query {query_id} processed!\n")
            
        except Exception as e:
            print(f"\n❌ processed error: {e}\n")
            self.queries[query_id] = {
                "query": query,
                "status": "error",
                "error": str(e),
            }
        
        return query_id
    
    def get_results(self, query_id: str) -> dict:
        """get query results"""
        return self.queries.get(query_id)
    
    def get_papers(self, query_id: str = None) -> list:
        """get papers for a query"""
        if query_id and query_id in self.queries:
            return self.queries[query_id].get("papers", [])
        return []
    
    def add_paper(self, paper: dict, query_id: str = None) -> str:
        """add a new paper"""
        import uuid
        paper_id = str(uuid.uuid4())
        
        if query_id and query_id in self.queries:
            self.queries[query_id]["papers"].append({
                "paper_id": paper_id,
                **paper,
            })
        
        return paper_id
    
    def update_paper(self, paper_id: str, updates: dict):
        """update paper information"""
        for query_results in self.queries.values():
            for paper in query_results.get("papers", []):
                if paper.get("paper_id") == paper_id:
                    paper.update(updates)
    
    def delete_paper(self, paper_id: str):
        """delete a paper by ID"""
        for query_results in self.queries.values():
            papers = query_results.get("papers", [])
            query_results["papers"] = [p for p in papers if p.get("paper_id") != paper_id]
    
    def get_summary(self, query_id: str) -> dict:
        """get comprehensive summary"""
        if query_id in self.queries:
            return self.queries[query_id].get("synthesis", {})
        return None


def main():
    """main function"""
    from src.ui.web_app import create_app
    from src.ui.api import create_api
    
    # initialize config
    config = get_config()
    config.validate()
    
    # create research engine
    engine = ResearchEngine(config)
    
    # create Web app
    app = create_app(config)
    
    # register API
    api = create_api(app, engine)
    app.register_blueprint(api)
    
    # run app
    print(f"\n🚀 Start ML Research Copilot")
    print(f"📍 access website: http://{config.HOST}:{config.PORT}")
    print(f"🔧 Debug mode: {config.DEBUG}\n")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
    )


if __name__ == "__main__":
    # for testing purposes
    config = get_config()
    engine = ResearchEngine(config)
    
    
    test_query = "deep-research 或者当前的AI联网搜索中，在拿到了目标网页之后，都是如何如何抽取有效信息组成答案的"
    query_id = engine.process_query(test_query)
    
    results = engine.get_results(query_id)
    if results:
        print(f"\n📋 results summary:")
        print(f"  status: {results.get('status')}")
        print(f"  papers count: {len(results.get('papers', []))}")
        if results.get('synthesis'):
            print(f"  synthesis summary: {results['synthesis'].get('summary', '')[:100]}...")
