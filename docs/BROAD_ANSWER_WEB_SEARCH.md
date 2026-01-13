# Broad Answer Generation with Web Search + LLM Synthesis

## Overview

The enhanced `BroadAnswerGenerator` module combines **web search** with **LLM synthesis** to generate comprehensive, up-to-date research answers. This solves the problem of LLM knowledge cutoff dates by augmenting LLM knowledge with current web information.

## Problem Statement

**Original Issue:**
- Step 2 (Intent Understanding) returns multiple refined academic questions
- Step 3 (Broad Answer Generation) used LLM-only approach → answers were outdated and too broad
- LLM knowledge cutoff (typically mid-2023 or 2024) meant missing recent developments

**Solution:**
- Add web search before LLM synthesis
- Collect recent, relevant information from the web
- Use LLM to synthesize web results + its knowledge into comprehensive answers
- Extract key concepts, developments, and authoritative sources

## Architecture

```
User Query (Multiple Refined Questions)
        ↓
        ├─→ [Web Search] → Collect recent information
        ├─→ [Format] → Prepare search results
        ├─→ [LLM Synthesis] → Combine with LLM knowledge
        └─→ [Parse] → Extract concepts, sources, developments
                ↓
            Comprehensive Broad Answer
            - Summary (current + knowledge-based)
            - Key Concepts
            - Recent Developments
            - Authoritative Sources
            - Web Search Results Used
```

## Usage

### Basic Usage (Web Search + LLM)

```python
from core.broad_answer_generation import BroadAnswerGenerator
from llm.client import LLMClient

# Initialize LLM client
llm_client = LLMClient(provider="openai", model="gpt-4")

# Create generator with web search enabled (default)
generator = BroadAnswerGenerator(
    llm_client=llm_client,
    enable_web_search=True,
    num_search_results=5
)

# Generate broad answer
query = "What are the latest developments in large language models?"
answer = generator.generate(query)

# Access results
print(answer.summary)                      # Main answer text
print(answer.key_concepts)                 # List of key concepts
print(answer.recent_developments)          # Recent trends identified
print(answer.authoritative_sources)        # Sources mentioned
print(answer.search_results)               # Web search results used
```

### LLM-Only Mode (Legacy)

```python
# Disable web search for LLM-only mode
generator = BroadAnswerGenerator(
    llm_client=llm_client,
    enable_web_search=False
)

answer = generator.generate("What is BERT?")
```

### Web Search Only

```python
from core.web_search import WebSearcher

searcher = WebSearcher()
results = searcher.search("Transformer models in NLP", num_results=5)

for result in results:
    print(f"- {result.title}")
    print(f"  URL: {result.url}")
    print(f"  Snippet: {result.snippet}")
```

### Using Google Custom Search (More Results)

```python
# Set environment variables:
# GOOGLE_API_KEY=your_api_key
# GOOGLE_SEARCH_ENGINE_ID=your_engine_id

from core.web_search import GoogleSearcher

searcher = GoogleSearcher()
results = searcher.search("attention mechanisms", num_results=5)
```

## API Reference

### BroadAnswerGenerator

#### `__init__(llm_client=None, enable_web_search=True, num_search_results=5)`

Initialize the broad answer generator.

**Parameters:**
- `llm_client`: LLM client instance (OpenAI, Papyrus, etc.)
- `enable_web_search` (bool): Enable web search integration (default: True)
- `num_search_results` (int): Number of web results to collect (default: 5)

#### `generate(query, context=None) → BroadAnswer`

Generate a comprehensive broad answer.

**Parameters:**
- `query` (str): User's research question
- `context` (str, optional): Background information

**Returns:** `BroadAnswer` object with:
- `summary`: Main answer text
- `problem`: Problem statement (if identified)
- `key_concepts`: List of key concepts
- `recent_developments`: Recent trends/developments
- `authoritative_sources`: Mentioned authoritative sources
- `search_results`: SearchResult objects used

### WebSearcher

#### `search(query, num_results=5) → List[SearchResult]`

Search the web using DuckDuckGo (free, no API key required).

**Returns:** List of SearchResult objects with:
- `title`: Result title
- `url`: Result URL
- `snippet`: Brief summary
- `source`: Source identifier (duckduckgo_instant, duckduckgo_related)

### GoogleSearcher

#### `search(query, num_results=5) → List[SearchResult]`

Search using Google Custom Search (requires API credentials).

## Response Format

The LLM is prompted to return structured output:

```xml
<response>
  <answer>Comprehensive answer synthesizing web results and knowledge</answer>
  <key_concepts>List of key concepts and definitions</key_concepts>
  <recent_developments>Recent trends and developments mentioned</recent_developments>
  <authoritative_sources>Key sources and authorities mentioned</authoritative_sources>
</response>
```

## Configuration

### Enable/Disable Web Search

```python
# Always use web search
generator = BroadAnswerGenerator(llm_client, enable_web_search=True)

# Never use web search
generator = BroadAnswerGenerator(llm_client, enable_web_search=False)
```

### Adjust Number of Search Results

```python
# More results for broader coverage
generator = BroadAnswerGenerator(llm_client, num_search_results=10)

# Fewer results for faster processing
generator = BroadAnswerGenerator(llm_client, num_search_results=3)
```

### Use Google Custom Search

Set environment variables:
```bash
export GOOGLE_API_KEY=sk-...
export GOOGLE_SEARCH_ENGINE_ID=xxx
```

Then `get_searcher()` will prefer Google:
```python
from core.web_search import get_searcher
searcher = get_searcher(prefer_google=True)
```

## Templates

The module uses templates from `src/templates/` for prompt management:

- `broad_answer_synthesis.json`: Main template for web search + LLM synthesis
- Includes system prompt, synthesis prompt, and result formatting

To customize prompts, edit `src/templates/broad_answer_synthesis.json`:

```json
{
  "system_prompt": "...",
  "synthesis_prompt": "...",
  "search_result_template": "..."
}
```

## Examples

Run examples from the project root:

```bash
# Example 1: Web search only
python examples/broad_answer_with_web_search_example.py --example 1

# Example 2: LLM-only (legacy)
python examples/broad_answer_with_web_search_example.py --example 2

# Example 3: Web search + LLM (recommended)
python examples/broad_answer_with_web_search_example.py --example 3

# Example 4: Compare approaches
python examples/broad_answer_with_web_search_example.py --example 4

# Example 5: Multiple queries
python examples/broad_answer_with_web_search_example.py --example 5
```

## Integration with Intent Understanding Pipeline

### Full Pipeline: Intent → Broad Answer → Paper Search

```python
from core.intent_understanding import IntentUnderstanding
from core.broad_answer_generation import BroadAnswerGenerator
from llm.client import LLMClient

# Initialize components
llm_client = LLMClient(provider="openai")
intent_module = IntentUnderstanding(llm_client)
broad_answer_module = BroadAnswerGenerator(
    llm_client,
    enable_web_search=True,
    num_search_results=5
)

# User query
user_query = "How do transformer models work in machine learning?"

# Step 2: Understand intent + generate research questions
intent = intent_module.understand(user_query)
print(f"Intent Type: {intent.intent_type}")
print(f"Research Area: {intent.research_area}")
print(f"Refined Questions: {intent.research_questions}")

# Step 3: Generate broad answer with web search
broad_answer = broad_answer_module.generate(
    query=intent.research_questions[0],  # Use first refined question
    context=intent.research_area
)
print(f"\nBroad Answer: {broad_answer.summary}")
print(f"Key Concepts: {broad_answer.key_concepts}")
print(f"Sources Used: {len(broad_answer.search_results)} web results")

# Step 4-7: Continue with paper retrieval, extraction, synthesis...
```

## Performance Considerations

### Web Search Performance
- **DuckDuckGo**: ~1-2 seconds per search, no API key required
- **Google Custom Search**: ~0.5-1 second per search, requires API key and quota

### LLM Synthesis
- Processing time increases with number of search results
- Typical: 5 results → 2-5 seconds for GPT-4 synthesis

### Optimization Tips
- Use `num_search_results=3-5` for balance of coverage and speed
- Cache results if same query is used multiple times
- Parallelize LLM calls for multiple queries
- Use faster models (GPT-3.5 Turbo) for quick summaries

## Troubleshooting

### Web Search Returns No Results
```python
# Check internet connection
# Verify DuckDuckGo API is accessible
# Try with different query terms
results = searcher.search("What is X", num_results=10)
```

### LLM Synthesis Fails
```python
# Check LLM client configuration
# Verify API key is set
# Ensure sufficient token limits
answer = broad_answer_module.generate(query, context=None)
```

### Parse Errors in Response
```python
# Check if LLM follows output format with XML tags
# Fallback returns raw response as summary
# Review template formatting in broad_answer_synthesis.json
```

## Dependencies

Required (already in requirements.txt):
- `requests>=2.31.0` — For web searches
- `openai>=1.0.0` — For LLM access

Optional:
- `google-api-client` — For Google Custom Search (install separately if needed)

## Future Enhancements

- [ ] Caching of search results to reduce API calls
- [ ] Multi-language support for searches
- [ ] Citation tracking (sentence-level attribution)
- [ ] Confidence scoring for synthesized statements
- [ ] Integration with academic search APIs (arXiv, Semantic Scholar)
- [ ] Asynchronous web search for faster processing
- [ ] Rate limiting and backoff strategies

## Related Modules

- `src/core/intent_understanding.py` — Generates refined research questions
- `src/core/web_search.py` — Web search utilities
- `src/templates/broad_answer_synthesis.json` — Prompt templates
- `examples/broad_answer_with_web_search_example.py` — Usage examples
