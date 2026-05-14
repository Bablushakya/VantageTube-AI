"""
VantageTube AI - Centralized AI Request Orchestrator
=====================================================
Single entry point for all Gemini API calls across the platform.

Key responsibilities:
- Batch multiple AI sub-tasks into one Gemini prompt (3 calls → 1)
- Serialize all calls per user via asyncio.Semaphore(1)
- Enforce global cooldown after 429 errors
- Two-layer cache: L1 TTLCache (in-memory) + L2 Supabase (persistent)
- Quota enforcement via QuotaManager
- Exponential-backoff retry for transient errors

Usage:
    from app.services.ai_orchestrator import ai_orchestrator
    from app.services.ai_bundles import VideoAnalysisBundle

    bundle = VideoAnalysisBundle(user_id, topic, keywords)
    result = await ai_orchestrator.submit_bundle(user_id, bundle)
    titles      = result.results["titles"]
    description = result.results["description"]
    tags        = result.results["tags"]
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES  (Task 2)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AITask:
    """
    A single AI sub-task within a bundle.

    Attributes:
        task_type:        Logical name of the output (e.g. "titles", "description", "tags").
                          Used as the key in BundleResult.results and as the JSON field name
                          in the batch prompt response.
        prompt_params:    Dict of parameters forwarded into the prompt template
                          (e.g. {"topic": "...", "keywords": [...], "tone": "engaging"}).
        estimated_tokens: Rough token estimate for quota pre-check.
                          Titles ≈ 1500, description ≈ 2000, tags ≈ 1000.
    """
    task_type:        str
    prompt_params:    Dict[str, Any]
    estimated_tokens: int


@dataclass
class TaskBundle:
    """
    A named collection of AITask objects submitted together to the orchestrator.

    The orchestrator will attempt to merge all compatible tasks into a single
    Gemini prompt, minimising quota consumption.

    Attributes:
        bundle_type: Logical name of the bundle (e.g. "video_analysis", "generator").
                     Used for logging and as part of the cache key.
        user_id:     The authenticated user's ID.  Used for per-user semaphore
                     and quota tracking.
        tasks:       Ordered list of AITask objects.  Must contain at least one task.
        cache_ttl:   How long (seconds) to cache the result.  Default 24 hours.
    """
    bundle_type: str
    user_id:     str
    tasks:       List[AITask]
    cache_ttl:   int = field(default=86_400)   # 24 hours


@dataclass
class BundleResult:
    """
    The result returned by AIOrchestrator.submit_bundle().

    Attributes:
        results:           Dict mapping each task_type to its output dict.
                           A value of None means the sub-task output was missing
                           from the Gemini response (partial failure).
        cache_hit:         True if the result was served from cache (L1 or L2)
                           without making any Gemini API call.
        gemini_calls_made: Number of Gemini API calls made for this bundle.
                           Should be 0 on cache hit, 1 on a successful batch call.
        total_tokens_used: Actual tokens consumed (from response metadata) or
                           the sum of estimated_tokens if metadata is unavailable.
    """
    results:           Dict[str, Any]
    cache_hit:         bool
    gemini_calls_made: int
    total_tokens_used: int


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR CLASS  (Tasks 3 + 4)
# ─────────────────────────────────────────────────────────────────────────────

class AIOrchestrator:
    """
    Centralized AI request orchestrator (singleton).

    All Gemini API calls across the platform flow through this class.
    It handles batching, per-user serialization, cooldown, caching,
    quota enforcement, and retry logic.
    """

    # ── Constants ─────────────────────────────────────────────────────────────
    _MIN_CALL_INTERVAL: float = 2.0    # seconds between consecutive Gemini calls
    _L1_MAX_SIZE:       int   = 500    # max entries in the in-memory TTL cache
    _L1_TTL:            int   = 300    # seconds — 5-minute L1 TTL
    _CACHE_TTL:         int   = 86_400 # seconds — 24-hour L2 TTL (default)

    # Phrases that identify a non-retryable Gemini quota/rate-limit error
    _QUOTA_PHRASES = (
        "quota exceeded",
        "you exceeded your current quota",
        "resource_exhausted",
        "generativelanguage.googleapis.com",
        "free_tier",
        "retry_delay",
        "429",
    )

    # ── Initialization ────────────────────────────────────────────────────────

    def __init__(self) -> None:
        # Per-user asyncio semaphores — created lazily on first use
        self._user_semaphores: Dict[str, asyncio.Semaphore] = {}

        # Global cooldown state — set after a 429 response
        # Value is a time.monotonic() timestamp; 0.0 means no cooldown active
        self._cooldown_until: float = 0.0

        # Monotonic timestamp of the last Gemini API call — enforces 2s gap
        self._last_call: float = 0.0

        # L1 in-memory TTL cache (cachetools)
        try:
            from cachetools import TTLCache
            self._l1_cache: Any = TTLCache(
                maxsize=self._L1_MAX_SIZE, ttl=self._L1_TTL
            )
        except ImportError:
            logger.warning("cachetools not installed — L1 cache disabled, all checks hit DB")
            self._l1_cache: Any = {}

        # Lazy-loaded Supabase client and Gemini model
        self._supabase = None
        self._gemini_model = None
        self._gemini_model_name: str = "unknown"

        # Load Gemini model at startup (non-blocking — errors are logged, not raised)
        self._init_gemini()

        logger.info("AIOrchestrator initialised")

    def _init_gemini(self) -> None:
        """Initialise the Gemini model, trying models in preference order."""
        try:
            from app.core.config import settings
            import google.generativeai as genai

            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not set — Gemini calls will fail at runtime")
                return

            genai.configure(api_key=settings.GEMINI_API_KEY)

            for model_name in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"):
                try:
                    self._gemini_model = genai.GenerativeModel(model_name)
                    self._gemini_model_name = model_name
                    logger.info(f"AIOrchestrator: Gemini model initialised → {model_name}")
                    return
                except Exception as exc:
                    logger.warning(f"AIOrchestrator: Could not init {model_name}: {exc}")

            logger.error("AIOrchestrator: No Gemini model could be initialised")

        except Exception as exc:
            logger.error(f"AIOrchestrator: Gemini init failed: {exc}")

    def _get_supabase(self):
        """Lazy-load the Supabase client to avoid circular imports at module load."""
        if self._supabase is None:
            from app.core.supabase import get_supabase
            self._supabase = get_supabase()
        return self._supabase

    # ── 3.2  Per-user semaphore ───────────────────────────────────────────────

    def _get_user_semaphore(self, user_id: str) -> asyncio.Semaphore:
        """
        Return (creating lazily if needed) a per-user asyncio.Semaphore(1).

        This serialises all Gemini calls for a single user so that concurrent
        browser tabs or rapid button clicks never trigger simultaneous requests
        for the same account.
        """
        if user_id not in self._user_semaphores:
            self._user_semaphores[user_id] = asyncio.Semaphore(1)
        return self._user_semaphores[user_id]

    # ── 3.3  Global inter-call rate limit ────────────────────────────────────

    async def _enforce_rate_limit(self) -> None:
        """
        Ensure at least _MIN_CALL_INTERVAL seconds pass between consecutive
        Gemini API calls.  This is a process-wide guard — independent of the
        per-user semaphore — because the Gemini free-tier limit is global.
        """
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._MIN_CALL_INTERVAL:
            wait = self._MIN_CALL_INTERVAL - elapsed
            logger.debug(
                f"Rate-limit pause: {wait:.2f}s  model={self._gemini_model_name}"
            )
            await asyncio.sleep(wait)
        self._last_call = time.monotonic()

    # ── 3.4  Cooldown check ───────────────────────────────────────────────────

    def _check_cooldown(self) -> None:
        """
        Raise HTTP 429 with a Retry-After header if the orchestrator is
        currently in a cooldown period (set by _handle_429 after a 429 response).
        """
        from fastapi import HTTPException

        remaining = self._cooldown_until - time.monotonic()
        if remaining > 0:
            retry_after = math.ceil(remaining)
            logger.debug(f"Cooldown active — {retry_after}s remaining")
            raise HTTPException(
                status_code=429,
                detail=(
                    f"AI service is in cooldown after a rate-limit error. "
                    f"Please wait {retry_after} seconds before retrying."
                ),
                headers={"Retry-After": str(retry_after)},
            )

    # ── 3.5  429 handler ─────────────────────────────────────────────────────

    def _handle_429(self, exc: Exception, user_id: str = "") -> None:
        """
        Extract the Retry-After delay from a Gemini 429 error and set the
        global cooldown timestamp.

        Parsing strategy (in order):
        1. Regex: "retry in <N>s" or "retry in <N.M>s"
        2. Regex: "retry_delay { seconds: <N> }"
        3. Default: 60 seconds
        """
        error_str = str(exc)

        match = re.search(r'retry in (\d+(?:\.\d+)?)\s*s', error_str, re.IGNORECASE)
        if match:
            retry_after = max(1, math.ceil(float(match.group(1))))
        else:
            match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', error_str)
            if match:
                retry_after = max(1, int(match.group(1)))
            else:
                retry_after = 60

        self._cooldown_until = time.monotonic() + retry_after

        uid_prefix = user_id[:8] if user_id else "unknown"
        logger.warning(
            f"Gemini 429 — user={uid_prefix}…  cooldown={retry_after}s  "
            f"detail: {error_str[:200]}"
        )

    # ── Quota error classifier ────────────────────────────────────────────────

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        """
        Return True if the exception is a Gemini quota / rate-limit error.
        These errors must NOT be retried — they won't resolve on retry.
        """
        msg = str(exc).lower()
        return any(phrase in msg for phrase in AIOrchestrator._QUOTA_PHRASES)

    @staticmethod
    def _gemini_retry_after(exc: Exception) -> int:
        """
        Extract the retry delay (seconds) from a Gemini 429 error message.
        Falls back to 60 if not parseable.
        """
        error_str = str(exc)
        match = re.search(r'retry in (\d+(?:\.\d+)?)\s*s', error_str, re.IGNORECASE)
        if match:
            return max(1, math.ceil(float(match.group(1))))
        match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', error_str)
        if match:
            return max(1, int(match.group(1)))
        return 60

    # ── 4.1  Bundle cache key ─────────────────────────────────────────────────

    def _hash_bundle(self, bundle: TaskBundle) -> str:
        """
        Compute a deterministic SHA-256 cache key for a TaskBundle.

        The key is built from:
          bundle_type + ":" + JSON of the merged prompt_params across all tasks
          (keys sorted so parameter order never affects the hash).

        This means two bundles with the same logical content but different dict
        insertion order will always share the same cache entry.
        """
        merged: Dict[str, Any] = {}
        for task in bundle.tasks:
            merged.update(task.prompt_params)

        payload = bundle.bundle_type + ":" + json.dumps(merged, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _hash_task(task: AITask) -> str:
        """
        Compute a per-task cache key for independent sub-task retrieval.
        SHA-256 of task_type + ":" + sorted prompt_params JSON.
        """
        payload = task.task_type + ":" + json.dumps(task.prompt_params, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    # ── 4.3  Cache read ───────────────────────────────────────────────────────

    async def _get_cached(
        self,
        user_id: str,
        cache_key: str,
    ) -> Optional[Dict]:
        """
        Two-layer cache lookup.

        L1 (in-memory TTLCache, 300s TTL):
            - Zero DB round-trip on hit.
            - Keyed by "{user_id}:{cache_key}".

        L2 (Supabase ai_cache table, 24h TTL):
            - Checked on L1 miss.
            - Populates L1 on hit.
            - Stale entries (age >= 86,400s) are deleted and treated as misses.

        Returns the cached result dict, or None on miss / any error.
        """
        l1_key = f"{user_id}:{cache_key}"

        # ── L1 check ──────────────────────────────────────────────────────────
        cached = self._l1_cache.get(l1_key)
        if cached is not None:
            logger.debug(f"Cache L1 HIT  user={user_id[:8]}…  key={cache_key[:12]}…")
            return cached

        # ── L2 check ──────────────────────────────────────────────────────────
        try:
            sb = self._get_supabase()
            resp = (
                sb.table("ai_cache")
                .select("result, created_at")
                .eq("user_id", user_id)
                .eq("prompt_hash", cache_key)
                .execute()
            )

            if resp.data:
                entry = resp.data[0]
                created_raw = entry["created_at"].replace("Z", "+00:00")
                created_at = datetime.fromisoformat(created_raw)

                now_utc = datetime.now(timezone.utc)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                age_seconds = (now_utc - created_at).total_seconds()

                if age_seconds < self._CACHE_TTL:
                    result = json.loads(entry["result"])
                    self._l1_cache[l1_key] = result
                    logger.debug(f"Cache L2 HIT  user={user_id[:8]}…  key={cache_key[:12]}…")
                    return result
                else:
                    # Stale — delete silently
                    sb.table("ai_cache").delete().eq("user_id", user_id).eq(
                        "prompt_hash", cache_key
                    ).execute()
                    logger.debug(f"Cache L2 STALE deleted  user={user_id[:8]}…")

        except Exception as exc:
            logger.warning(f"Cache L2 read error (fail open): {exc}")

        return None

    # ── 4.4  Cache write ──────────────────────────────────────────────────────

    async def _set_cached(
        self,
        user_id: str,
        cache_key: str,
        result: Dict,
        tasks: List[AITask],
    ) -> None:
        """
        Write result to both cache layers.

        Writes:
        1. Batch result under the bundle cache key (content_type="video_analysis_batch").
        2. Each sub-task's output under its own per-task cache key so individual
           sub-tasks can be retrieved independently on future requests.

        All DB write errors are silently ignored — a cache write failure must
        never cause the generation request to fail.
        """
        l1_key = f"{user_id}:{cache_key}"
        self._l1_cache[l1_key] = result

        # Get Supabase client once for all L2 writes
        try:
            sb = self._get_supabase()
        except Exception as exc:
            logger.warning(f"Cache L2 unavailable (ignored): {exc}")
            return

        # ── L2 batch write ────────────────────────────────────────────────────
        try:
            sb.table("ai_cache").upsert(
                {
                    "user_id":      user_id,
                    "content_type": "video_analysis_batch",
                    "prompt_hash":  cache_key,
                    "result":       json.dumps(result),
                    "created_at":   datetime.utcnow().isoformat(),
                },
                on_conflict="user_id,content_type,prompt_hash",
            ).execute()
            logger.debug(
                f"Cache L2 WRITE batch  user={user_id[:8]}…  key={cache_key[:12]}…"
            )
        except Exception as exc:
            logger.warning(f"Cache L2 batch write error (ignored): {exc}")

        # ── L2 per-task sub-key writes ────────────────────────────────────────
        for task in tasks:
            sub_result = result.get(task.task_type)
            if sub_result is None:
                continue

            task_key = self._hash_task(task)
            task_l1_key = f"{user_id}:{task_key}"
            self._l1_cache[task_l1_key] = sub_result

            try:
                sb.table("ai_cache").upsert(
                    {
                        "user_id":      user_id,
                        "content_type": task.task_type,
                        "prompt_hash":  task_key,
                        "result":       json.dumps(sub_result),
                        "created_at":   datetime.utcnow().isoformat(),
                    },
                    on_conflict="user_id,content_type,prompt_hash",
                ).execute()
                logger.debug(
                    f"Cache L2 WRITE sub-task={task.task_type}  "
                    f"user={user_id[:8]}…  key={task_key[:12]}…"
                )
            except Exception as exc:
                logger.warning(f"Cache L2 sub-task write error (ignored): {exc}")


    # ── 6.1  submit_bundle — main public entry point ─────────────────────────

    async def submit_bundle(
        self,
        user_id: str,
        bundle: TaskBundle,
    ) -> BundleResult:
        """
        Submit a TaskBundle for AI generation.

        This is the single entry point for all Gemini API calls across the
        platform.  It orchestrates the full lifecycle:

        1. Validate the bundle has at least one task.
        2. Check the two-layer cache (L1 TTLCache → L2 Supabase).
        3. Acquire the per-user semaphore (serialises concurrent requests).
        4. Check the global cooldown (set after a 429 response).
        5. Check per-user quota via QuotaManager.
        6. Execute the batch Gemini call.
        7. Record quota usage.
        8. Write result to both cache layers.
        9. Return a BundleResult.

        Args:
            user_id: Authenticated user's ID.
            bundle:  TaskBundle with at least one AITask.

        Returns:
            BundleResult with results dict, cache_hit flag, call count, tokens.

        Raises:
            ValueError:        If bundle.tasks is empty.
            HTTPException(429): If in cooldown or quota exceeded.
            HTTPException(500): If Gemini call fails after all retries.
        """
        from fastapi import HTTPException
        from app.services.ai_quota_manager import quota_manager, QuotaStatus

        t_start = time.monotonic()

        # ── Step 1: Validate ──────────────────────────────────────────────────
        if not bundle.tasks:
            raise ValueError(
                f"Bundle '{bundle.bundle_type}' must contain at least one task"
            )

        logger.info(
            f"submit_bundle  bundle={bundle.bundle_type}  "
            f"user={user_id[:8]}...  tasks={[t.task_type for t in bundle.tasks]}"
        )

        # ── Step 2: Cache check ───────────────────────────────────────────────
        cache_key = self._hash_bundle(bundle)
        cached = await self._get_cached(user_id, cache_key)
        if cached is not None:
            elapsed_ms = (time.monotonic() - t_start) * 1000
            logger.info(
                f"submit_bundle CACHE HIT  bundle={bundle.bundle_type}  "
                f"user={user_id[:8]}...  elapsed={elapsed_ms:.1f}ms"
            )
            return BundleResult(
                results=cached,
                cache_hit=True,
                gemini_calls_made=0,
                total_tokens_used=0,
            )

        # ── Steps 3–8: Acquire semaphore, check cooldown, call Gemini ─────────
        gemini_calls_made = 0
        total_tokens = 0

        async with self._get_user_semaphore(user_id):

            # Step 4: Cooldown check (inside semaphore — serialised per user)
            self._check_cooldown()

            # Step 5: Quota pre-check
            estimated_tokens = sum(t.estimated_tokens for t in bundle.tasks)
            quota_status, quota_message = await quota_manager.check_quota(
                user_id=user_id,
                estimated_tokens=estimated_tokens,
            )
            if quota_status != QuotaStatus.AVAILABLE:
                logger.warning(
                    f"Quota check failed  user={user_id[:8]}...  "
                    f"status={quota_status.value}  msg={quota_message}"
                )
                from app.api.content import _retry_after_from_message
                raise HTTPException(
                    status_code=429,
                    detail=f"Quota exceeded: {quota_message}",
                    headers={"Retry-After": _retry_after_from_message(quota_message)},
                )

            # Step 6: Execute batch Gemini call
            try:
                raw_result = await self._execute_batch(bundle.tasks)
                gemini_calls_made = 1
                total_tokens = estimated_tokens  # use estimate; metadata not always available
            except HTTPException:
                raise  # 429 from cooldown or quota — propagate as-is
            except Exception as exc:
                # Check for Gemini quota/rate-limit errors BEFORE wrapping in 500.
                # These must surface as 429 so the frontend can show a countdown.
                if self._is_quota_error(exc):
                    self._handle_429(exc, user_id)
                    retry_after = self._gemini_retry_after(exc)
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            f"AI generation quota exceeded. "
                            f"Please wait {retry_after} seconds before trying again. "
                            f"(Gemini free tier limit reached)"
                        ),
                        headers={"Retry-After": str(retry_after)},
                    )
                logger.error(
                    f"submit_bundle FAILED  bundle={bundle.bundle_type}  "
                    f"user={user_id[:8]}...  error={str(exc)[:200]}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"AI generation failed: {str(exc)[:300]}",
                )

            # Step 7: Record quota usage
            quota_manager.record_request(user_id=user_id, tokens_used=total_tokens)

            # Step 8: Write to cache
            await self._set_cached(user_id, cache_key, raw_result, bundle.tasks)

        # ── Step 9: Return result ─────────────────────────────────────────────
        elapsed_ms = (time.monotonic() - t_start) * 1000
        logger.info(
            f"submit_bundle DONE  bundle={bundle.bundle_type}  "
            f"user={user_id[:8]}...  calls={gemini_calls_made}  "
            f"tokens={total_tokens}  elapsed={elapsed_ms:.1f}ms"
        )

        return BundleResult(
            results=raw_result,
            cache_hit=False,
            gemini_calls_made=gemini_calls_made,
            total_tokens_used=total_tokens,
        )

    # ── 5.1  Build batch prompt ───────────────────────────────────────────────

    def _build_batch_prompt(self, tasks: List[AITask]) -> str:
        """
        Build a single Gemini prompt that requests all task outputs in one call.

        The prompt uses a fixed JSON schema so _parse_batch_response can
        reliably extract each sub-task's output.  Supported task types:
          - "titles"      → list of {title, seo_score, reasoning}
          - "description" → {description, seo_tips}
          - "tags"        → {primary_tags, secondary_tags, long_tail_tags,
                             broad_tags, all_tags}

        Unknown task types are included as free-form string fields so the
        orchestrator stays extensible without code changes.
        """
        # Collect shared params (topic, keywords, tone) from the first task
        # that has them — all tasks in a VideoAnalysisBundle share these.
        shared: Dict[str, Any] = {}
        for task in tasks:
            for key in ("topic", "keywords", "tone", "target_audience"):
                if key in task.prompt_params and key not in shared:
                    shared[key] = task.prompt_params[key]

        topic    = shared.get("topic", "")
        keywords = shared.get("keywords", [])
        tone     = shared.get("tone", "engaging")
        kw_str   = ", ".join(keywords) if keywords else "none"

        # Per-task count params
        title_count = next(
            (t.prompt_params.get("count", 5) for t in tasks if t.task_type == "titles"),
            5,
        )
        tag_count = next(
            (t.prompt_params.get("count_tags", 20) for t in tasks if t.task_type == "tags"),
            20,
        )

        # Build the JSON schema section dynamically from the task list
        schema_parts: List[str] = []
        for task in tasks:
            if task.task_type == "titles":
                schema_parts.append(
                    f'  "titles": [{{"title": "...", "seo_score": 85, "reasoning": "..."}}]'
                    f'  // generate exactly {title_count} items'
                )
            elif task.task_type == "description":
                schema_parts.append(
                    '  "description": {"description": "...", "seo_tips": ["tip1", "tip2"]}'
                )
            elif task.task_type == "tags":
                schema_parts.append(
                    f'  "tags": {{"primary_tags": [], "secondary_tags": [], '
                    f'"long_tail_tags": [], "broad_tags": [], "all_tags": []}}'
                    f'  // generate exactly {tag_count} total tags'
                )
            else:
                schema_parts.append(f'  "{task.task_type}": "..."')

        schema_str = ",\n".join(schema_parts)

        prompt = f"""Generate the following for a YouTube video about "{topic}":
Keywords: {kw_str}
Tone: {tone}

Return ONLY a valid JSON object with these exact keys (no markdown, no extra text):
{{
{schema_str}
}}

Rules for titles:
- Generate exactly {title_count} titles
- Each title 50-60 characters
- Include primary keyword naturally
- Compelling but not clickbait
- seo_score is an integer 0-100
- reasoning is one sentence

Rules for description:
- First line: compelling hook (50-100 chars)
- Weave in keywords naturally
- Scannable with line breaks
- Include subscribe/like call-to-action
- 3-5 actionable SEO tips

Rules for tags:
- Generate exactly {tag_count} total tags across all categories
- 1-3 words each, no duplicates
- all_tags must contain every tag from all categories combined"""

        return prompt

    # ── 5.2  Parse batch response ─────────────────────────────────────────────

    def _parse_batch_response(
        self,
        text: str,
        tasks: List[AITask],
    ) -> Dict[str, Any]:
        """
        Extract each task's output from the Gemini batch response.

        Strategy:
        1. Find the first '{' and last '}' in the response text.
        2. Parse the JSON between them.
        3. For each task, extract data.get(task.task_type) — None if missing.
        4. On any JSON parse failure, return {task_type: None} for all tasks.

        Missing fields are logged at WARNING level but never raise — a partial
        result is always better than a 500 error.
        """
        # Find JSON boundaries
        start = text.find("{")
        end   = text.rfind("}") + 1

        if start == -1 or end <= start:
            logger.warning(
                f"Batch response contains no JSON object — returning nulls. "
                f"Response preview: {text[:200]!r}"
            )
            return {t.task_type: None for t in tasks}

        try:
            data = json.loads(text[start:end])
        except json.JSONDecodeError as exc:
            logger.warning(
                f"Batch response JSON parse failed: {exc} — returning nulls. "
                f"Response preview: {text[start:start+200]!r}"
            )
            return {t.task_type: None for t in tasks}

        result: Dict[str, Any] = {}
        for task in tasks:
            value = data.get(task.task_type)
            if value is None:
                logger.warning(
                    f"Batch response missing field: {task.task_type!r}"
                )
            result[task.task_type] = value

        return result

    # ── 5.3  Execute batch ────────────────────────────────────────────────────

    async def _execute_batch(self, tasks: List[AITask]) -> Dict[str, Any]:
        """
        Build a single batch prompt, call Gemini, and return the parsed result.

        Flow:
        1. Enforce the 2-second global inter-call rate limit.
        2. Build the batch prompt via _build_batch_prompt.
        3. Call Gemini via asyncio.to_thread (non-blocking).
        4. On 429/quota error: call _handle_429 then re-raise immediately.
        5. On transient error: delegate to RetryStrategy (max 3 retries).
        6. Parse and return the response via _parse_batch_response.

        Returns a dict mapping task_type → output (None for missing fields).
        """
        from app.services.ai_quota_manager import retry_strategy

        if not self._gemini_model:
            raise RuntimeError(
                "Gemini model not initialised — check GEMINI_API_KEY in .env"
            )

        prompt = self._build_batch_prompt(tasks)
        estimated = sum(t.estimated_tokens for t in tasks)

        async def _call_gemini() -> Dict[str, Any]:
            await self._enforce_rate_limit()
            logger.debug(
                f"Gemini batch call  model={self._gemini_model_name}  "
                f"tasks={[t.task_type for t in tasks]}  "
                f"estimated_tokens={estimated}"
            )
            try:
                response = await asyncio.to_thread(
                    self._gemini_model.generate_content, prompt  # type: ignore[union-attr]
                )
                return self._parse_batch_response(response.text, tasks)
            except Exception as exc:
                if self._is_quota_error(exc):
                    # 429 / quota — set cooldown and re-raise immediately (no retry)
                    self._handle_429(exc)
                    raise
                raise  # transient — let RetryStrategy handle it

        return await retry_strategy.execute_with_retry(
            _call_gemini,
            retryable_exceptions=(Exception,),
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
ai_orchestrator = AIOrchestrator()
