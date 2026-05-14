"""
Property-Based Tests for AIOrchestrator using Hypothesis.

Each test encodes a formal correctness property that must hold for ALL valid
inputs, not just the specific examples in test_ai_orchestrator.py.

Properties covered:
  P2: VideoAnalysisBundle always batches into at most one Gemini call
  P3: Cache hit on repeated identical bundle
  P5: Per-user serialization
  P6: Cache key is parameter-order-independent  (already in unit tests, repeated here)
  P7: Quota error classification is exhaustive for known phrases
  P9: Backward-compatible response schema for existing endpoints

Gemini API calls are mocked with AsyncMock — tests are fast and free.

Run with:
    cd vantagetube-ai/backend
    python -m pytest tests/test_ai_orchestrator_properties.py -v
"""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.services.ai_orchestrator import AIOrchestrator, AITask, TaskBundle, BundleResult
from app.services.ai_bundles import VideoAnalysisBundle
from app.services.ai_quota_manager import QuotaStatus


# ── Shared mock Gemini response ───────────────────────────────────────────────
_MOCK_BATCH_RESULT = {
    "titles": [{"title": "Test Title", "seo_score": 85, "reasoning": "Good"}],
    "description": {"description": "Test description", "seo_tips": ["tip1"]},
    "tags": {
        "primary_tags": ["test"], "secondary_tags": [], "long_tail_tags": [],
        "broad_tags": [], "all_tags": ["test"],
    },
}


def _make_orch() -> AIOrchestrator:
    """Create a fresh orchestrator instance for each test."""
    return AIOrchestrator()


def _mock_quota_manager():
    """Return a mock QuotaManager that always allows requests."""
    mock = MagicMock()
    mock.check_quota = AsyncMock(return_value=(QuotaStatus.AVAILABLE, "OK"))
    mock.record_request = MagicMock()
    return mock


# ── Hypothesis strategies ─────────────────────────────────────────────────────

# Valid non-empty topic strings (printable ASCII, no control chars)
topic_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=80,
)

# Keyword lists (0–5 short words)
keywords_strategy = st.lists(
    st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20),
    max_size=5,
)

# Title count 1–10
count_strategy = st.integers(min_value=1, max_value=10)

# User IDs (UUID-like strings)
user_id_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=8,
    max_size=36,
)


# ─────────────────────────────────────────────────────────────────────────────
# Property 2: VideoAnalysisBundle always batches into at most one Gemini call
# Feature: ai-request-orchestration, Property 2
# ─────────────────────────────────────────────────────────────────────────────

class TestProperty2BatchingInvariant:
    """
    P2: For any valid VideoAnalysisBundle, submit_bundle returns a BundleResult
    where gemini_calls_made <= 1.

    This is the core optimization invariant: three logically separate outputs
    (titles, description, tags) are always produced by at most one Gemini call.

    Validates: Requirements 2.1, 2.2, 11.2
    """

    @given(
        topic=topic_strategy,
        keywords=keywords_strategy,
        count=count_strategy,
        user_id=user_id_strategy,
    )
    @settings(max_examples=50, deadline=None)
    def test_video_analysis_bundle_at_most_one_gemini_call(
        self, topic, keywords, count, user_id
    ):
        """P2: gemini_calls_made <= 1 for any valid VideoAnalysisBundle."""
        orch = _make_orch()
        bundle = VideoAnalysisBundle(user_id, topic, keywords, count=count)

        async def run():
            with patch.object(orch, "_execute_batch", new=AsyncMock(return_value=_MOCK_BATCH_RESULT)), \
                 patch.object(orch, "_set_cached", new=AsyncMock()), \
                 patch.object(orch, "_get_cached", new=AsyncMock(return_value=None)), \
                 patch("app.services.ai_quota_manager.quota_manager", _mock_quota_manager()):
                return await orch.submit_bundle(user_id, bundle)

        result = asyncio.get_event_loop().run_until_complete(run())

        assert isinstance(result, BundleResult)
        assert result.gemini_calls_made <= 1, (
            f"Expected <= 1 Gemini call, got {result.gemini_calls_made} "
            f"for topic={topic!r}"
        )

    @given(
        topic=topic_strategy,
        user_id=user_id_strategy,
    )
    @settings(max_examples=30, deadline=None)
    def test_bundle_result_has_all_required_fields(self, topic, user_id):
        """P8: BundleResult always contains all required fields."""
        orch = _make_orch()
        bundle = VideoAnalysisBundle(user_id, topic)

        async def run():
            with patch.object(orch, "_execute_batch", new=AsyncMock(return_value=_MOCK_BATCH_RESULT)), \
                 patch.object(orch, "_set_cached", new=AsyncMock()), \
                 patch.object(orch, "_get_cached", new=AsyncMock(return_value=None)), \
                 patch("app.services.ai_quota_manager.quota_manager", _mock_quota_manager()):
                return await orch.submit_bundle(user_id, bundle)

        result = asyncio.get_event_loop().run_until_complete(run())

        assert result.results is not None
        assert isinstance(result.cache_hit, bool)
        assert isinstance(result.gemini_calls_made, int)
        assert result.gemini_calls_made >= 0
        assert isinstance(result.total_tokens_used, int)
        assert result.total_tokens_used >= 0


# ─────────────────────────────────────────────────────────────────────────────
# Property 3: Cache hit on repeated identical bundle
# Feature: ai-request-orchestration, Property 3
# ─────────────────────────────────────────────────────────────────────────────

class TestProperty3CacheHit:
    """
    P3: Submitting the same bundle twice returns cache_hit=True on the second call.

    This is a round-trip property: write-then-read must return the cached value.

    Validates: Requirements 5.1, 5.2, 5.3
    """

    @given(
        topic=topic_strategy,
        keywords=keywords_strategy,
        user_id=user_id_strategy,
    )
    @settings(max_examples=30, deadline=None)
    def test_second_identical_bundle_is_cache_hit(self, topic, keywords, user_id):
        """P3: Second call with same bundle returns cache_hit=True, gemini_calls_made=0."""
        orch = _make_orch()
        bundle1 = VideoAnalysisBundle(user_id, topic, keywords)
        bundle2 = VideoAnalysisBundle(user_id, topic, keywords)

        call_count = {"n": 0}

        async def mock_execute(tasks):
            call_count["n"] += 1
            return _MOCK_BATCH_RESULT

        async def run():
            with patch.object(orch, "_execute_batch", new=mock_execute), \
                 patch("app.services.ai_quota_manager.quota_manager", _mock_quota_manager()):
                r1 = await orch.submit_bundle(user_id, bundle1)
                r2 = await orch.submit_bundle(user_id, bundle2)
                return r1, r2

        r1, r2 = asyncio.get_event_loop().run_until_complete(run())

        assert r1.cache_hit is False, "First call should not be a cache hit"
        assert r2.cache_hit is True, "Second identical call should be a cache hit"
        assert r2.gemini_calls_made == 0, "Cache hit should make 0 Gemini calls"
        assert call_count["n"] == 1, "Gemini should only be called once"


# ─────────────────────────────────────────────────────────────────────────────
# Property 5: Per-user serialization
# Feature: ai-request-orchestration, Property 5
# ─────────────────────────────────────────────────────────────────────────────

class TestProperty5PerUserSerialization:
    """
    P5: Two concurrent submit_bundle calls for the same user are serialized.
    The second call does not begin its Gemini call until the first completes.

    Validates: Requirements 3.1, 3.2, 3.3
    """

    @given(user_id=user_id_strategy)
    @settings(max_examples=20, deadline=None)
    def test_concurrent_calls_same_user_are_serialized(self, user_id):
        """P5: Concurrent calls for same user execute sequentially."""
        orch = _make_orch()
        bundle = VideoAnalysisBundle(user_id, "Python tips")

        call_log = []

        async def slow_batch(tasks):
            call_log.append("start")
            await asyncio.sleep(0.02)
            call_log.append("end")
            return _MOCK_BATCH_RESULT

        async def run():
            with patch.object(orch, "_execute_batch", new=slow_batch), \
                 patch.object(orch, "_set_cached", new=AsyncMock()), \
                 patch("app.services.ai_quota_manager.quota_manager", _mock_quota_manager()):
                await asyncio.gather(
                    orch.submit_bundle(user_id, bundle),
                    orch.submit_bundle(user_id, bundle),
                )

        asyncio.get_event_loop().run_until_complete(run())

        # Serialised: start-end-start-end (NOT start-start-end-end)
        # Second call hits L1 cache after first completes, so only 1 Gemini call
        # The important invariant: no "start" appears before the previous "end"
        for i, event in enumerate(call_log):
            if event == "start" and i > 0:
                assert call_log[i - 1] == "end", (
                    f"Concurrent execution detected: {call_log}"
                )

    @given(
        user_id_a=user_id_strategy,
        user_id_b=user_id_strategy,
    )
    @settings(max_examples=20)
    def test_different_users_do_not_block_each_other(self, user_id_a, user_id_b):
        """P5 corollary: Different users have independent semaphores."""
        assume(user_id_a != user_id_b)

        orch = _make_orch()
        sem_a = orch._get_user_semaphore(user_id_a)
        sem_b = orch._get_user_semaphore(user_id_b)

        assert sem_a is not sem_b, (
            f"Users {user_id_a!r} and {user_id_b!r} should have different semaphores"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Property 6: Cache key is parameter-order-independent
# Feature: ai-request-orchestration, Property 6
# ─────────────────────────────────────────────────────────────────────────────

class TestProperty6CacheKeyOrderIndependent:
    """
    P6: Reordering the keys in prompt_params produces the same cache key.

    Validates: Requirements 5.4
    """

    @given(
        params=st.dictionaries(
            keys=st.text(min_size=1, max_size=10,
                         alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
            values=st.text(min_size=0, max_size=20),
            min_size=1,
            max_size=8,
        )
    )
    @settings(max_examples=100)
    def test_hash_task_is_order_independent(self, params):
        """P6: _hash_task produces same hash regardless of dict key order."""
        # Create two tasks with same params but different insertion order
        keys = list(params.keys())
        reversed_params = {k: params[k] for k in reversed(keys)}

        t1 = AITask("titles", params, 1500)
        t2 = AITask("titles", reversed_params, 1500)

        h1 = AIOrchestrator._hash_task(t1)
        h2 = AIOrchestrator._hash_task(t2)

        assert h1 == h2, (
            f"Hash mismatch for same params in different order: "
            f"{params} vs {reversed_params}"
        )

    @given(
        topic=topic_strategy,
        keywords=keywords_strategy,
    )
    @settings(max_examples=50)
    def test_hash_bundle_is_order_independent(self, topic, keywords):
        """P6: _hash_bundle produces same hash for semantically equivalent bundles."""
        orch = _make_orch()

        b1 = VideoAnalysisBundle("u1", topic, keywords)
        b2 = VideoAnalysisBundle("u1", topic, list(reversed(keywords)))

        # Keywords order in the list matters for content but not for the hash
        # (the hash merges all params — keyword list order is preserved in JSON)
        # What we test here is that dict key order doesn't matter
        t1 = AITask("titles", {"topic": topic, "keywords": keywords, "tone": "engaging", "count": 5}, 1500)
        t2 = AITask("titles", {"count": 5, "tone": "engaging", "keywords": keywords, "topic": topic}, 1500)
        bundle_a = TaskBundle("video_analysis", "u1", [t1])
        bundle_b = TaskBundle("video_analysis", "u1", [t2])

        assert orch._hash_bundle(bundle_a) == orch._hash_bundle(bundle_b)


# ─────────────────────────────────────────────────────────────────────────────
# Property 7: Quota error classification is exhaustive for known phrases
# Feature: ai-request-orchestration, Property 7
# ─────────────────────────────────────────────────────────────────────────────

class TestProperty7QuotaErrorClassification:
    """
    P7: Any error message containing a known quota phrase is classified as
    a non-retryable quota error.

    Validates: Requirements 7.2, 7.3
    """

    QUOTA_PHRASES = [
        "quota exceeded",
        "you exceeded your current quota",
        "resource_exhausted",
        "generativelanguage.googleapis.com",
        "free_tier",
        "retry_delay",
        "429",
    ]

    @given(
        phrase=st.sampled_from(QUOTA_PHRASES),
        prefix=st.text(max_size=50),
        suffix=st.text(max_size=50),
    )
    @settings(max_examples=100)
    def test_known_phrase_always_classified_as_quota_error(self, phrase, prefix, suffix):
        """P7: Any message containing a known quota phrase is a quota error."""
        msg = prefix + phrase + suffix
        exc = Exception(msg)
        assert AIOrchestrator._is_quota_error(exc), (
            f"Expected quota error for message containing {phrase!r}: {msg!r}"
        )

    @given(
        phrase=st.sampled_from(QUOTA_PHRASES),
        prefix=st.text(max_size=20),
        suffix=st.text(max_size=20),
    )
    @settings(max_examples=50)
    def test_classification_is_case_insensitive(self, phrase, prefix, suffix):
        """P7: Quota error classification is case-insensitive."""
        msg = prefix + phrase.upper() + suffix
        exc = Exception(msg)
        assert AIOrchestrator._is_quota_error(exc), (
            f"Case-insensitive check failed for {phrase.upper()!r}"
        )

    @given(
        msg=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
            min_size=5,
            max_size=100,
        )
    )
    @settings(max_examples=50)
    def test_random_non_quota_message_not_classified(self, msg):
        """P7 inverse: Random messages without quota phrases are not quota errors."""
        # Only test messages that don't accidentally contain a quota phrase
        msg_lower = msg.lower()
        has_quota_phrase = any(p in msg_lower for p in [p.lower() for p in self.QUOTA_PHRASES])
        assume(not has_quota_phrase)

        exc = Exception(msg)
        assert not AIOrchestrator._is_quota_error(exc), (
            f"False positive quota error for: {msg!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Property 9: Backward-compatible response schema
# Feature: ai-request-orchestration, Property 9
# ─────────────────────────────────────────────────────────────────────────────

class TestProperty9BackwardCompatibility:
    """
    P9: The existing endpoint response schemas are unchanged after the
    orchestrator is introduced.

    Validates: Requirements 11.1
    """

    @given(
        topic=topic_strategy,
        count=count_strategy,
    )
    @settings(max_examples=30)
    def test_generated_titles_schema_unchanged(self, topic, count):
        """P9: GeneratedTitles always has titles, topic, keywords, generated_at."""
        from app.models.content import GeneratedTitles, GeneratedTitle
        from datetime import datetime

        titles = [
            GeneratedTitle(text=f"Title {i}", score=80, reasoning="Good")
            for i in range(count)
        ]
        response = GeneratedTitles(
            titles=titles,
            topic=topic,
            keywords=[],
            generated_at=datetime.utcnow(),
        )

        assert len(response.titles) == count
        assert response.topic == topic
        assert isinstance(response.keywords, list)
        assert isinstance(response.generated_at, datetime)

    @given(
        description=st.text(min_size=0, max_size=500),
        seo_tips=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    )
    @settings(max_examples=30)
    def test_generated_description_schema_unchanged(self, description, seo_tips):
        """P9: GeneratedDescription always has description, word_count, seo_tips."""
        from app.models.content import GeneratedDescription
        from datetime import datetime

        response = GeneratedDescription(
            description=description,
            word_count=len(description.split()),
            includes_timestamps=True,
            includes_links=True,
            includes_cta=True,
            seo_tips=seo_tips,
            generated_at=datetime.utcnow(),
        )

        assert response.description == description
        assert response.word_count == len(description.split())
        assert response.seo_tips == seo_tips

    @given(
        tags=st.lists(
            st.text(min_size=1, max_size=20,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
            min_size=0,
            max_size=20,
        )
    )
    @settings(max_examples=30)
    def test_generated_tags_schema_unchanged(self, tags):
        """P9: GeneratedTags always has tags, tag_count, tag_categories."""
        from app.models.content import GeneratedTags
        from datetime import datetime

        response = GeneratedTags(
            tags=tags,
            tag_count=len(tags),
            tag_categories={"primary": tags[:3], "secondary": tags[3:]},
            generated_at=datetime.utcnow(),
        )

        assert response.tags == tags
        assert response.tag_count == len(tags)
        assert isinstance(response.tag_categories, dict)
