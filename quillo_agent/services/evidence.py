"""
Evidence retrieval service - Web search and fact extraction

Evidence Layer v1: Manual-only, sourced, non-authorial evidence retrieval.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import httpx
import re
import uuid
from urllib.parse import urlparse, quote_plus
from loguru import logger

from quillo_agent.schemas import EvidenceFact, EvidenceSource, EvidenceResponse
from quillo_agent.services.llm import LLMRouter
from quillo_agent.config import settings


# Initialize LLM router
llm_router = LLMRouter()


# Hard limits per spec
MAX_FACTS = 10
MAX_SOURCES = 8
SEARCH_TIMEOUT = 10.0
FETCH_TIMEOUT = 5.0

# Disallowed persuasion phrases (for linting)
PERSUASION_PHRASES = [
    "you should",
    "recommend",
    "best option",
    "therefore",
    "i think you should",
    "i suggest",
    "it's recommended",
    "my recommendation",
]


def _is_persuasive(text: str) -> bool:
    """Check if text contains persuasion language (case-insensitive)"""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in PERSUASION_PHRASES)


def _detect_empty_reason(query: str, search_results: List[Dict[str, Any]], extracted_facts: List[Dict[str, Any]]) -> str:
    """
    Detect why evidence retrieval returned empty results.

    Evidence Guards v1.1: Heuristic-based detection to help users understand why no facts were found.

    Args:
        query: The search query
        search_results: Search results from web search
        extracted_facts: Facts extracted from results

    Returns:
        One of: computed_stat, ambiguous_query, source_fetch_blocked, no_results, unknown
    """
    query_lower = query.lower()

    # Check for computed statistics
    computed_indicators = ["percentage", "percent", "%", "rate", "ratio", "average", "mean"]
    if any(indicator in query_lower for indicator in computed_indicators):
        return "computed_stat"

    # Check for ambiguous queries (sports + year patterns)
    # Common pattern: team/league name + year (could mean season or calendar year)
    sports_indicators = ["season", "league", "championship", "wins", "losses", "draws", "points"]
    year_pattern = re.search(r'\b(19|20)\d{2}\b', query_lower)
    if year_pattern and any(indicator in query_lower for indicator in sports_indicators):
        return "ambiguous_query"

    # Check if we got search results but failed to extract facts
    # This suggests source fetching or parsing issues
    if len(search_results) > 0 and len(extracted_facts) == 0:
        return "source_fetch_blocked"

    # No search results at all
    if len(search_results) == 0:
        return "no_results"

    # Unknown reason
    return "unknown"


async def _search_web(query: str) -> List[Dict[str, Any]]:
    """
    Perform web search and return results.

    Uses DuckDuckGo HTML search (no API key required).
    Returns list of results with title, url, snippet.
    """
    try:
        # Use DuckDuckGo HTML search
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(
                search_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            response.raise_for_status()
            html = response.text

        # Parse search results (simple regex-based extraction)
        results = []

        # Extract result blocks - DuckDuckGo uses specific patterns
        # This is a simple parser for v1; could be enhanced with BeautifulSoup
        result_pattern = r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<a[^>]+class="result__snippet"[^>]*>([^<]+)</a>'

        links = re.findall(result_pattern, html)
        snippets = re.findall(snippet_pattern, html)

        for i, (url, title) in enumerate(links[:MAX_SOURCES]):
            # Clean up URL (DuckDuckGo wraps URLs)
            if url.startswith('//duckduckgo.com/l/?'):
                # Extract actual URL from redirect
                continue

            snippet = snippets[i] if i < len(snippets) else ""

            results.append({
                "title": title.strip(),
                "url": url.strip(),
                "snippet": snippet.strip(),
                "domain": urlparse(url).netloc
            })

        logger.info(f"Search returned {len(results)} results for query: {query[:50]}")
        return results[:MAX_SOURCES]

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


async def _extract_facts_from_results(
    query: str,
    results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Use LLM to extract neutral facts from search results.

    Returns list of facts with text, source_id, and optional published_at.
    """
    if not results:
        return []

    # Build context from search results
    results_text = "\n\n".join([
        f"Source {i+1}:\nTitle: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for i, r in enumerate(results)
    ])

    # Prompt for neutral fact extraction
    system_prompt = """You are a fact extraction system. Extract ONLY neutral, verifiable facts from the provided search results.

CRITICAL RULES:
- Extract 6-10 factual statements (max 10)
- Each fact must be neutral and verifiable
- NO advice, recommendations, or conclusions
- NO persuasion language: "you should", "recommend", "best option", "therefore", etc.
- Include source number for each fact
- Optionally include publication date if clearly stated

Format each fact as:
FACT: [Neutral statement]
SOURCE: [Source number 1-8]
DATE: [YYYY-MM-DD or "unknown"]

Example:
FACT: The Python 3.12 release was announced on October 2, 2023.
SOURCE: 1
DATE: 2023-10-02

Extract facts now."""

    user_prompt = f"""Query: {query}

Search Results:
{results_text}

Extract 6-10 neutral facts from these results. Follow the format strictly."""

    try:
        # Call LLM for fact extraction using OpenRouter
        model = llm_router._get_openrouter_model(tier="fast")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await llm_router._openrouter_chat(
            messages=messages,
            model=model,
            max_tokens=2000,
            timeout=10.0
        )

        if not response:
            logger.error("LLM returned empty response")
            return []

        # Parse response
        facts = []
        current_fact = {}

        for line in response.strip().split('\n'):
            line = line.strip()
            if line.startswith('FACT:'):
                if current_fact and 'text' in current_fact:
                    facts.append(current_fact)
                current_fact = {'text': line[5:].strip()}
            elif line.startswith('SOURCE:'):
                try:
                    source_num = int(line[7:].strip())
                    current_fact['source_num'] = source_num
                except ValueError:
                    current_fact['source_num'] = 1
            elif line.startswith('DATE:'):
                date_str = line[5:].strip()
                if date_str.lower() != 'unknown':
                    current_fact['date'] = date_str

        # Add last fact
        if current_fact and 'text' in current_fact:
            facts.append(current_fact)

        # Validate and filter facts
        validated_facts = []
        for fact in facts[:MAX_FACTS]:
            # Check for persuasion language
            if _is_persuasive(fact.get('text', '')):
                logger.warning(f"Filtered persuasive fact: {fact['text'][:50]}")
                continue

            validated_facts.append(fact)

        logger.info(f"Extracted {len(validated_facts)} validated facts")
        return validated_facts[:MAX_FACTS]

    except Exception as e:
        logger.error(f"Fact extraction failed: {e}")
        return []


async def retrieve_evidence(query: str) -> EvidenceResponse:
    """
    Retrieve evidence for a query.

    Main entry point for evidence retrieval. Performs web search,
    extracts neutral facts, and returns structured evidence response.

    Args:
        query: Search query string

    Returns:
        EvidenceResponse with facts, sources, and metadata
    """
    start_time = datetime.now(timezone.utc)
    retrieved_at = start_time.isoformat()

    try:
        # Validate query
        if not query or not query.strip():
            return EvidenceResponse(
                ok=False,
                retrieved_at=retrieved_at,
                duration_ms=0,
                facts=[],
                sources=[],
                error="Query cannot be empty"
            )

        # Step 1: Web search
        search_results = await _search_web(query.strip())

        if not search_results:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            empty_reason = _detect_empty_reason(query.strip(), [], [])
            return EvidenceResponse(
                ok=True,
                retrieved_at=retrieved_at,
                duration_ms=duration_ms,
                facts=[],
                sources=[],
                limits="No search results found for this query.",
                empty_reason=empty_reason
            )

        # Step 2: Extract facts from results
        extracted_facts = await _extract_facts_from_results(query, search_results)

        # Step 3: Build sources list
        sources = []
        for i, result in enumerate(search_results[:MAX_SOURCES]):
            source = EvidenceSource(
                id=f"s{i+1}",
                title=result.get('title', 'Untitled'),
                domain=result.get('domain', 'unknown'),
                url=result.get('url', ''),
                retrieved_at=retrieved_at
            )
            sources.append(source)

        # Step 4: Build facts list with source references
        facts = []
        for fact_data in extracted_facts[:MAX_FACTS]:
            source_num = fact_data.get('source_num', 1)
            source_id = f"s{min(source_num, len(sources))}"

            fact = EvidenceFact(
                text=fact_data.get('text', ''),
                source_id=source_id,
                published_at=fact_data.get('date')
            )
            facts.append(fact)

        # Calculate duration
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Build limits note and empty_reason if needed
        limits_note = None
        empty_reason = None
        if len(facts) == 0:
            limits_note = "No facts could be extracted from search results."
            empty_reason = _detect_empty_reason(query.strip(), search_results, extracted_facts)
        elif len(facts) < 6:
            limits_note = "Limited results available for this query."

        return EvidenceResponse(
            ok=True,
            retrieved_at=retrieved_at,
            duration_ms=duration_ms,
            facts=facts,
            sources=sources,
            limits=limits_note,
            empty_reason=empty_reason
        )

    except Exception as e:
        logger.error(f"Evidence retrieval failed: {e}")
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        return EvidenceResponse(
            ok=False,
            retrieved_at=retrieved_at,
            duration_ms=duration_ms,
            facts=[],
            sources=[],
            error="Evidence fetch failed. Please try again."
        )
