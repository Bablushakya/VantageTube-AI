"""
Unit tests for AIOrchestrator internals and bundle factories.

Covers Tasks 12.1 – 12.5:
  12.1  VideoAnalysisBundle factory — correct task types and token estimates
  12.2  _parse_batch_response — field routing and None for missing/invalid JSON
  12.3  _handle_429 — cooldown set correctly for various error message formats
  12.4  _hash_bundle — identical hashes for semantically equivalent bundles
  12.5  /generate/video-analysis endpoint — schema and backward compat

Run with:
    cd vantagetube-ai/backend
    python -m pytest tests/test_ai_orchestrator.py -v
"""

import asyncio
import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Imports ───────────────────────────────────────────────────────────────────
from app.services.ai_orchestrator import AIOrchestrator, AITask, TaskBundle, BundleResult
from app.services.ai_bundles import VideoAnalysisBundle, GeneratorBundle


# ─────────────────────────────────────────────────────────────────────────────
# 12.1  VideoAnalysisBundle factory
# ─────────────────────────────────────────────────────────────────────────────

class TestVideoAnalysisBundle:
    """12.1 — VideoAnalysisBundle returns correct task types and token estimates."""

    def test_bundle_type(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        assert b.bundle_type == "video_analysis"

    def test_user_id(self):
        b = VideoAnalysisBundle("user-abc", "Python tips")
        assert b.user_id == "user-abc"

    def test_task_types_in_order(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        assert [t.task_type for t in b.tasks] == ["titles", "description", "tags"]

    def test_token_estimates(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        estimates = [t.estimated_tokens for t in b.tasks]
        assert estimates == [1500, 2000, 1000]

    def test_total_tokens(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        assert sum(t.estimated_tokens for t in b.tasks) == 4500

    def test_title_count_param(self):
        b = VideoAnalysisBundle("u1", "Python tips", count=7)
        titles_task = next(t for t in b.tasks if t.task_type == "titles")
        assert titles_task.prompt_params["count"] == 7

    def test_tags_count_param(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        tags_task = next(t for t in b.tasks if t.task_type == "tags")
        assert tags_task.prompt_params["count_tags"] == 20

    def test_keywords_forwarded(self):
        b = VideoAnalysisBundle("u1", "Python tips", keywords=["python", "coding"])
        for task in b.tasks:
            assert task.prompt_params.get("keywords") == ["python", "coding"]

    def test_none_keywords_defaults_to_empty_list(self):
        b = VideoAnalysisBundle("u1", "Python tips", keywords=None)
        for task in b.tasks:
            assert task.prompt_params.get("keywords") == []

    def test_cache_ttl_is_24h(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        assert b.cache_ttl == 86_400

    def test_three_tasks(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        assert len(b.tasks) == 3


class TestGeneratorBundle:
    """12.1 — GeneratorBundle returns correct task types and token estimates."""

    def test_bundle_type(self):
        g = GeneratorBundle("u1", "Python tips")
        assert g.bundle_type == "generator"

    def test_task_types_in_order(self):
        g = GeneratorBundle("u1", "Python tips")
        assert [t.task_type for t in g.tasks] == ["hook", "outline", "cta"]

    def test_token_estimates(self):
        g = GeneratorBundle("u1", "Python tips")
        assert [t.estimated_tokens for t in g.tasks] == [800, 1500, 500]

    def test_total_tokens(self):
        g = GeneratorBundle("u1", "Python tips")
        assert sum(t.estimated_tokens for t in g.tasks) == 2800


# ─────────────────────────────────────────────────────────────────────────────
# 12.2  _parse_batch_response
# ─────────────────────────────────────────────────────────────────────────────

class TestParseBatchResponse:
    """12.2 — _parse_batch_response routes fields correctly."""

    def setup_method(self):
        self.orch = AIOrchestrator()
        self.tasks = [
            AITask("titles",      {"topic": "t"}, 1500),
            AITask("description", {"topic": "t"}, 2000),
            AITask("tags",        {"topic": "t"}, 1000),
        ]

    def _valid_json(self):
        return json.dumps({
            "titles": [{"title": "T1", "seo_score": 90, "reasoning": "r"}],
            "description": {"description": "Desc", "seo_tips": ["tip1"]},
            "tags": {"primary_tags": ["py"], "secondary_tags": [], "long_tail_tags": [],
                     "broad_tags": [], "all_tags": ["py"]},
        })

    def test_valid_json_routes_all_fields(self):
        result = self.orch._parse_batch_response(self._valid_json(), self.tasks)
        assert result["titles"][0]["title"] == "T1"
        assert result["description"]["description"] == "Desc"
        assert result["tags"]["all_tags"] == ["py"]

    def test_missing_field_returns_none(self):
        partial = json.dumps({"titles": [{"title": "T1", "seo_score": 90, "reasoning": "r"}]})
        result = self.orch._parse_batch_response(partial, self.tasks)
        assert result["titles"] is not None
        assert result["description"] is None
        assert result["tags"] is None

    def test_invalid_json_returns_all_none(self):
        result = self.orch._parse_batch_response("not json at all", self.tasks)
        assert all(v is None for v in result.values())

    def test_empty_string_returns_all_none(self):
        result = self.orch._parse_batch_response("", self.tasks)
        assert all(v is None for v in result.values())

    def test_markdown_wrapped_json_is_parsed(self):
        wrapped = "```json\n" + self._valid_json() + "\n```"
        result = self.orch._parse_batch_response(wrapped, self.tasks)
        assert result["titles"] is not None

    def test_result_keys_match_task_types(self):
        result = self.orch._parse_batch_response(self._valid_json(), self.tasks)
        assert set(result.keys()) == {"titles", "description", "tags"}


# ─────────────────────────────────────────────────────────────────────────────
# 12.3  _handle_429
# ─────────────────────────────────────────────────────────────────────────────

class TestHandle429:
    """12.3 — _handle_429 sets _cooldown_until correctly."""

    def setup_method(self):
        self.orch = AIOrchestrator()
        self.orch._cooldown_until = 0.0

    def test_parses_retry_in_seconds(self):
        self.orch._handle_429(Exception("Please retry in 50.775381752s."), "user-abc")
        remaining = self.orch._cooldown_until - time.monotonic()
        assert 49 < remaining <= 52, f"Expected ~51s, got {remaining:.1f}s"

    def test_parses_retry_delay_block(self):
        self.orch._handle_429(Exception("retry_delay { seconds: 30 }"), "user-abc")
        remaining = self.orch._cooldown_until - time.monotonic()
        assert 28 < remaining <= 31, f"Expected ~30s, got {remaining:.1f}s"

    def test_defaults_to_60s_on_unparseable(self):
        self.orch._handle_429(Exception("some unknown error"), "user-abc")
        remaining = self.orch._cooldown_until - time.monotonic()
        assert 58 < remaining <= 61, f"Expected ~60s, got {remaining:.1f}s"

    def test_cooldown_is_set_in_future(self):
        before = time.monotonic()
        self.orch._handle_429(Exception("retry in 10s"), "user-abc")
        assert self.orch._cooldown_until > before

    def test_handles_empty_user_id(self):
        # Should not raise even with empty user_id
        self.orch._handle_429(Exception("retry in 5s"), "")
        assert self.orch._cooldown_until > time.monotonic()


# ─────────────────────────────────────────────────────────────────────────────
# 12.4  _hash_bundle
# ─────────────────────────────────────────────────────────────────────────────

class TestHashBundle:
    """12.4 — _hash_bundle produces identical hashes for equivalent bundles."""

    def setup_method(self):
        self.orch = AIOrchestrator()

    def _make_bundle(self, params_order: list) -> TaskBundle:
        """Create a bundle with params in the given key order."""
        tasks = [AITask("titles", dict(zip(params_order, ["Python", ["py"], "engaging", 5])), 1500)]
        return TaskBundle("video_analysis", "u1", tasks)

    def test_same_params_different_order_same_hash(self):
        t1 = AITask("titles", {"topic": "Python", "keywords": ["py"], "tone": "engaging", "count": 5}, 1500)
        t2 = AITask("titles", {"count": 5, "tone": "engaging", "keywords": ["py"], "topic": "Python"}, 1500)
        b1 = TaskBundle("video_analysis", "u1", [t1])
        b2 = TaskBundle("video_analysis", "u1", [t2])
        assert self.orch._hash_bundle(b1) == self.orch._hash_bundle(b2)

    def test_different_topic_different_hash(self):
        t1 = AITask("titles", {"topic": "Python"}, 1500)
        t2 = AITask("titles", {"topic": "JavaScript"}, 1500)
        b1 = TaskBundle("video_analysis", "u1", [t1])
        b2 = TaskBundle("video_analysis", "u1", [t2])
        assert self.orch._hash_bundle(b1) != self.orch._hash_bundle(b2)

    def test_different_bundle_type_different_hash(self):
        t = AITask("titles", {"topic": "Python"}, 1500)
        b1 = TaskBundle("video_analysis", "u1", [t])
        b2 = TaskBundle("generator", "u1", [t])
        assert self.orch._hash_bundle(b1) != self.orch._hash_bundle(b2)

    def test_hash_is_sha256_length(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        h = self.orch._hash_bundle(b)
        assert len(h) == 64  # SHA-256 hex digest

    def test_hash_is_deterministic(self):
        b = VideoAnalysisBundle("u1", "Python tips")
        assert self.orch._hash_bundle(b) == self.orch._hash_bundle(b)

    def test_hash_task_order_independent(self):
        t1 = AITask("titles", {"a": 1, "b": 2}, 1500)
        t2 = AITask("titles", {"b": 2, "a": 1}, 1500)
        assert AIOrchestrator._hash_task(t1) == AIOrchestrator._hash_task(t2)


# ─────────────────────────────────────────────────────────────────────────────
# 12.5  /generate/video-analysis endpoint schema
# ─────────────────────────────────────────────────────────────────────────────

class TestVideoAnalysisEndpoint:
    """12.5 — New endpoint returns VideoAnalysisResponse; existing endpoints unchanged."""

    @classmethod
    def setup_class(cls):
        """Load .env so Settings can initialise when importing content router."""
        import os
        from pathlib import Path
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path, override=False)

    def test_video_analysis_response_has_all_fields(self):
        from app.models.content import VideoAnalysisResponse
        fields = VideoAnalysisResponse.model_fields
        assert "titles" in fields
        assert "description" in fields
        assert "tags" in fields
        assert "cache_hit" in fields
        assert "gemini_calls_made" in fields
        assert "generated_at" in fields

    def test_existing_generated_titles_schema_unchanged(self):
        from app.models.content import GeneratedTitles, GeneratedTitle
        fields = GeneratedTitles.model_fields
        assert "titles" in fields
        assert "topic" in fields
        assert "keywords" in fields
        assert "generated_at" in fields

    def test_existing_generated_description_schema_unchanged(self):
        from app.models.content import GeneratedDescription
        fields = GeneratedDescription.model_fields
        assert "description" in fields
        assert "seo_tips" in fields
        assert "word_count" in fields

    def test_existing_generated_tags_schema_unchanged(self):
        from app.models.content import GeneratedTags
        fields = GeneratedTags.model_fields
        assert "tags" in fields
        assert "tag_count" in fields
        assert "tag_categories" in fields

    def test_video_analysis_request_validation(self):
        from app.models.content import VideoAnalysisRequest
        from pydantic import ValidationError

        # Valid
        req = VideoAnalysisRequest(topic="Python tips")
        assert req.count == 5
        assert req.tone == "engaging"
        assert req.keywords == []

        # count out of range
        with pytest.raises(ValidationError):
            VideoAnalysisRequest(topic="t", count=0)
        with pytest.raises(ValidationError):
            VideoAnalysisRequest(topic="t", count=11)

    def test_new_endpoint_registered(self):
        from app.api.content import router
        paths = [r.path for r in router.routes]
        assert "/content/generate/video-analysis" in paths

    def test_existing_endpoints_still_registered(self):
        from app.api.content import router
        paths = [r.path for r in router.routes]
        for path in [
            "/content/generate/titles",
            "/content/generate/description",
            "/content/generate/tags",
        ]:
            assert path in paths, f"Missing existing endpoint: {path}"
