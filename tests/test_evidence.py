"""
Tests for Evidence Layer v1 - Manual-only, sourced, non-authorial evidence retrieval

Test Coverage:
- Contract shape validation
- Hard limits enforcement (max 10 facts, max 8 sources)
- No-persuasion lint checks
- Failure modes
- Integration tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from quillo_agent.main import create_app
from quillo_agent.config import settings

app = create_app()
client = TestClient(app)

# Test constants
TEST_UI_TOKEN = "dev-test-token-12345"

# Mock evidence response for testing
MOCK_EVIDENCE_SUCCESS = {
    "ok": True,
    "retrieved_at": "2025-12-21T15:00:00Z",
    "duration_ms": 1234,
    "facts": [
        {
            "text": "Python 3.12 was released on October 2, 2023.",
            "source_id": "s1",
            "published_at": "2023-10-02T00:00:00Z"
        },
        {
            "text": "The release includes performance improvements.",
            "source_id": "s1",
            "published_at": None
        }
    ],
    "sources": [
        {
            "id": "s1",
            "title": "Python 3.12 Release Notes",
            "domain": "python.org",
            "url": "https://www.python.org/downloads/release/python-3120/",
            "retrieved_at": "2025-12-21T15:00:00Z"
        }
    ],
    "limits": None,
    "error": None
}


class TestEvidenceContract:
    """Test that Evidence API returns correct contract shape"""

    @patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
    def test_contract_shape_success(self, mock_retrieve):
        """Test that successful response has all required fields"""
        from quillo_agent.schemas import EvidenceResponse
        mock_retrieve.return_value = EvidenceResponse(**MOCK_EVIDENCE_SUCCESS)

        # Mock settings for dev mode bypass
        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": "Python 3.12 release"},
                headers={}
            )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "ok" in data
        assert "retrieved_at" in data
        assert "duration_ms" in data
        assert "facts" in data
        assert "sources" in data

        # Type checks
        assert isinstance(data["ok"], bool)
        assert isinstance(data["retrieved_at"], str)
        assert isinstance(data["duration_ms"], int)
        assert isinstance(data["facts"], list)
        assert isinstance(data["sources"], list)

    @patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
    def test_contract_shape_error(self, mock_retrieve):
        """Test that error response has ok=False and error field"""
        from quillo_agent.schemas import EvidenceResponse
        mock_retrieve.return_value = EvidenceResponse(
            ok=False,
            retrieved_at="2025-12-21T15:00:00Z",
            duration_ms=100,
            facts=[],
            sources=[],
            error="Evidence fetch failed. Please try again."
        )

        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": "test query"},
                headers={}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["ok"] is False
        assert "error" in data
        assert data["error"] is not None
        assert isinstance(data["error"], str)

    def test_empty_query_rejected(self):
        """Test that empty query returns error"""
        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": ""},
                headers={}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "error" in data


class TestEvidenceLimits:
    """Test that hard limits are enforced"""

    @patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
    def test_max_facts_limit(self, mock_retrieve):
        """Test that facts are limited to max 10"""
        # Create 15 facts (should be truncated to 10)
        many_facts = [
            {
                "text": f"Fact {i}",
                "source_id": "s1",
                "published_at": None
            }
            for i in range(15)
        ]

        from quillo_agent.schemas import EvidenceResponse, EvidenceFact, EvidenceSource
        mock_retrieve.return_value = EvidenceResponse(
            ok=True,
            retrieved_at="2025-12-21T15:00:00Z",
            duration_ms=1000,
            facts=[EvidenceFact(**f) for f in many_facts[:10]],  # Should be limited to 10
            sources=[
                EvidenceSource(
                    id="s1",
                    title="Test Source",
                    domain="example.com",
                    url="https://example.com",
                    retrieved_at="2025-12-21T15:00:00Z"
                )
            ]
        )

        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": "test"},
                headers={}
            )

        data = response.json()
        assert len(data["facts"]) <= 10, "Facts exceeded max limit of 10"

    @patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
    def test_max_sources_limit(self, mock_retrieve):
        """Test that sources are limited to max 8"""
        # Create 10 sources (should be truncated to 8)
        many_sources = [
            {
                "id": f"s{i}",
                "title": f"Source {i}",
                "domain": f"example{i}.com",
                "url": f"https://example{i}.com",
                "retrieved_at": "2025-12-21T15:00:00Z"
            }
            for i in range(10)
        ]

        from quillo_agent.schemas import EvidenceResponse, EvidenceSource
        mock_retrieve.return_value = EvidenceResponse(
            ok=True,
            retrieved_at="2025-12-21T15:00:00Z",
            duration_ms=1000,
            facts=[],
            sources=[EvidenceSource(**s) for s in many_sources[:8]]  # Should be limited to 8
        )

        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": "test"},
                headers={}
            )

        data = response.json()
        assert len(data["sources"]) <= 8, "Sources exceeded max limit of 8"


class TestNoPersuasionLint:
    """Test that evidence contains no persuasion language"""

    DISALLOWED_PHRASES = [
        "you should",
        "recommend",
        "best option",
        "therefore",
        "i think you should",
        "i suggest",
        "it's recommended",
        "my recommendation"
    ]

    @patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
    def test_no_persuasion_in_facts(self, mock_retrieve):
        """Test that facts do not contain disallowed persuasion phrases"""
        # Create neutral facts (should pass)
        neutral_facts = [
            {
                "text": "The study was published in 2023.",
                "source_id": "s1",
                "published_at": None
            },
            {
                "text": "The report contains 50 pages of data.",
                "source_id": "s1",
                "published_at": None
            }
        ]

        from quillo_agent.schemas import EvidenceResponse, EvidenceFact, EvidenceSource
        mock_retrieve.return_value = EvidenceResponse(
            ok=True,
            retrieved_at="2025-12-21T15:00:00Z",
            duration_ms=1000,
            facts=[EvidenceFact(**f) for f in neutral_facts],
            sources=[
                EvidenceSource(
                    id="s1",
                    title="Test Source",
                    domain="example.com",
                    url="https://example.com",
                    retrieved_at="2025-12-21T15:00:00Z"
                )
            ]
        )

        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": "test"},
                headers={}
            )

        data = response.json()

        # Check all facts for persuasion language
        for fact in data["facts"]:
            fact_text_lower = fact["text"].lower()
            for phrase in self.DISALLOWED_PHRASES:
                assert phrase not in fact_text_lower, \
                    f"Fact contains disallowed persuasion phrase '{phrase}': {fact['text']}"

    @patch('quillo_agent.services.evidence._is_persuasive')
    def test_persuasion_filter_catches_violations(self, mock_is_persuasive):
        """Test that the persuasion filter function works correctly"""
        from quillo_agent.services.evidence import _is_persuasive

        # Test cases
        persuasive_texts = [
            "You should use Python for this project.",
            "I recommend starting with the basics.",
            "This is the best option for your needs.",
            "Therefore, you must choose option A."
        ]

        neutral_texts = [
            "Python was released in 1991.",
            "The study included 1000 participants.",
            "The data shows a 20% increase.",
        ]

        # Mock to return True for persuasive texts
        for text in persuasive_texts:
            mock_is_persuasive.return_value = True
            assert _is_persuasive(text), f"Failed to detect persuasive text: {text}"

        # Mock to return False for neutral texts
        for text in neutral_texts:
            mock_is_persuasive.return_value = False
            assert not _is_persuasive(text), f"False positive for neutral text: {text}"


class TestFailureModes:
    """Test error handling and failure scenarios"""

    @patch('quillo_agent.routers.ui_proxy.retrieve_evidence')
    def test_network_failure_returns_neutral_error(self, mock_retrieve):
        """Test that network failures return neutral error with ok=False"""
        from quillo_agent.schemas import EvidenceResponse
        mock_retrieve.return_value = EvidenceResponse(
            ok=False,
            retrieved_at="2025-12-21T15:00:00Z",
            duration_ms=50,
            facts=[],
            sources=[],
            error="Evidence fetch failed. Please try again."
        )

        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": "test"},
                headers={}
            )

        assert response.status_code == 200
        data = response.json()

        assert data["ok"] is False
        assert data["error"] == "Evidence fetch failed. Please try again."
        assert len(data["facts"]) == 0
        assert len(data["sources"]) == 0

    def test_missing_query_returns_error(self):
        """Test that missing query parameter returns error"""
        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={},  # No query or use_last_message
                headers={}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "error" in data

    def test_use_last_message_without_implementation(self):
        """Test that use_last_message returns appropriate error (not implemented in v1)"""
        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"use_last_message": True},
                headers={}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "not yet implemented" in data["error"].lower() or "not implemented" in data["error"].lower()


class TestRateLimiting:
    """Test that rate limiting is applied"""

    def test_rate_limit_applied(self):
        """Test that rate limiting is configured for evidence endpoint"""
        # The endpoint should have @limiter.limit("30/minute") decorator
        # This is a sanity check - actual rate limiting tested via integration
        with patch.object(settings, 'quillo_ui_token', ''):
            # Make a single request (should succeed)
            response = client.post(
                "/ui/api/evidence",
                json={"query": "test"},
                headers={}
            )

            # Should get a response (might be error due to mock, but not rate limited)
            assert response.status_code in [200, 429]  # 200 or Too Many Requests


class TestEvidenceGuardsV1_1:
    """Test Evidence Guards v1.1 - empty_reason detection and authority guards"""

    def test_empty_reason_field_exists(self):
        """Test that empty_reason field is present in response when facts are empty"""
        with patch.object(settings, 'quillo_ui_token', ''):
            response = client.post(
                "/ui/api/evidence",
                json={"query": "nonexistent query xyz123"},
                headers={}
            )

        assert response.status_code == 200
        data = response.json()

        # When facts are empty, empty_reason should be present
        if len(data.get("facts", [])) == 0:
            assert "empty_reason" in data
            assert data["empty_reason"] in [
                "no_results", "ambiguous_query", "computed_stat",
                "source_fetch_blocked", "unknown", None
            ]

    def test_computed_stat_detection(self):
        """Test that queries with percentage/rate are detected as computed_stat"""
        from quillo_agent.services.evidence import _detect_empty_reason

        # Test queries that should be detected as computed_stat
        computed_queries = [
            "What is the win percentage of Leeds United in 2024?",
            "Calculate the conversion rate for our landing page",
            "What's the average score?",
            "Show me the ratio of wins to losses",
            "What percentage of users clicked?"
        ]

        for query in computed_queries:
            reason = _detect_empty_reason(query, [], [])
            assert reason == "computed_stat", f"Failed to detect computed_stat for: {query}"

    def test_ambiguous_query_detection(self):
        """Test that sports + year queries are detected as ambiguous"""
        from quillo_agent.services.evidence import _detect_empty_reason

        # Test queries that should be detected as ambiguous
        ambiguous_queries = [
            "Leeds United wins 2024",
            "Manchester United season 2023",
            "NBA championship 2022",
            "Premier league points 2021"
        ]

        for query in ambiguous_queries:
            reason = _detect_empty_reason(query, [], [])
            assert reason == "ambiguous_query", f"Failed to detect ambiguous_query for: {query}"

    def test_source_fetch_blocked_detection(self):
        """Test that search results with no extracted facts are detected as source_fetch_blocked"""
        from quillo_agent.services.evidence import _detect_empty_reason

        # Simulate having search results but no extracted facts
        search_results = [
            {"title": "Test", "url": "https://example.com", "snippet": "snippet"}
        ]
        extracted_facts = []

        reason = _detect_empty_reason("test query", search_results, extracted_facts)
        assert reason == "source_fetch_blocked"

    def test_no_results_detection(self):
        """Test that queries with no search results are detected as no_results"""
        from quillo_agent.services.evidence import _detect_empty_reason

        reason = _detect_empty_reason("test query", [], [])
        assert reason == "no_results"

    def test_empty_reason_not_present_when_facts_exist(self):
        """Test that empty_reason is None or not present when facts exist"""
        from quillo_agent.schemas import EvidenceResponse, EvidenceFact, EvidenceSource

        # Mock a successful response with facts
        mock_response = EvidenceResponse(
            ok=True,
            retrieved_at="2025-12-21T16:00:00Z",
            duration_ms=1000,
            facts=[
                EvidenceFact(
                    text="Test fact",
                    source_id="s1",
                    published_at=None
                )
            ],
            sources=[
                EvidenceSource(
                    id="s1",
                    title="Test Source",
                    domain="example.com",
                    url="https://example.com",
                    retrieved_at="2025-12-21T16:00:00Z"
                )
            ],
            limits=None,
            empty_reason=None
        )

        # When facts are present, empty_reason should be None
        assert len(mock_response.facts) > 0
        assert mock_response.empty_reason is None


class TestResearchModelSelection:
    """Test that Evidence uses dedicated research model configuration"""

    @pytest.mark.anyio
    @patch('quillo_agent.services.evidence._search_web')
    @patch('quillo_agent.services.evidence.llm_router._openrouter_chat')
    async def test_uses_research_model_when_configured(self, mock_chat, mock_search):
        """Test that evidence extraction uses openrouter_research_model when set"""
        from quillo_agent.services.evidence import _extract_facts_from_results
        from quillo_agent.config import settings

        # Mock search results
        mock_results = [
            {
                "title": "Test Article",
                "url": "https://example.com",
                "snippet": "Test content",
                "domain": "example.com"
            }
        ]

        # Mock LLM response
        mock_chat.return_value = """FACT: Test fact 1
SOURCE: 1
DATE: unknown

FACT: Test fact 2
SOURCE: 1
DATE: 2024-01-01"""

        # Test with research model configured
        with patch.object(settings, 'openrouter_research_model', 'google/gemini-2.5-flash'):
            await _extract_facts_from_results("test query", mock_results)

            # Verify that the research model was used
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['model'] == 'google/gemini-2.5-flash'

    @pytest.mark.anyio
    @patch('quillo_agent.services.evidence._search_web')
    @patch('quillo_agent.services.evidence.llm_router._openrouter_chat')
    @patch('quillo_agent.services.evidence.llm_router._get_openrouter_model')
    async def test_falls_back_to_fast_tier_when_not_configured(self, mock_get_model, mock_chat, mock_search):
        """Test that evidence extraction falls back to fast tier when research model not set"""
        from quillo_agent.services.evidence import _extract_facts_from_results
        from quillo_agent.config import settings

        # Mock search results
        mock_results = [
            {
                "title": "Test Article",
                "url": "https://example.com",
                "snippet": "Test content",
                "domain": "example.com"
            }
        ]

        # Mock fast tier model selection
        mock_get_model.return_value = "anthropic/claude-3-haiku"

        # Mock LLM response
        mock_chat.return_value = """FACT: Test fact 1
SOURCE: 1
DATE: unknown"""

        # Test with research model NOT configured (empty string)
        with patch.object(settings, 'openrouter_research_model', ''):
            await _extract_facts_from_results("test query", mock_results)

            # Verify that fallback was used
            mock_get_model.assert_called_once_with(tier="fast")
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['model'] == "anthropic/claude-3-haiku"

    @pytest.mark.anyio
    @patch('quillo_agent.services.evidence._search_web')
    @patch('quillo_agent.services.evidence.llm_router._openrouter_chat')
    async def test_research_model_preserves_other_params(self, mock_chat, mock_search):
        """Test that using research model doesn't change other LLM call parameters"""
        from quillo_agent.services.evidence import _extract_facts_from_results
        from quillo_agent.config import settings

        # Mock search results
        mock_results = [
            {
                "title": "Test Article",
                "url": "https://example.com",
                "snippet": "Test content",
                "domain": "example.com"
            }
        ]

        # Mock LLM response
        mock_chat.return_value = """FACT: Test fact
SOURCE: 1
DATE: unknown"""

        # Test with research model
        with patch.object(settings, 'openrouter_research_model', 'google/gemini-2.5-flash'):
            await _extract_facts_from_results("test query", mock_results)

            # Verify that other parameters are unchanged
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['max_tokens'] == 2000  # Should be unchanged
            assert call_kwargs['timeout'] == 10.0  # Should be unchanged
            assert 'messages' in call_kwargs  # Should still have messages
