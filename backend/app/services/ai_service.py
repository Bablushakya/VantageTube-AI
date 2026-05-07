
"""
VantageTube AI - AI Service
Handles AI-powered content generation with quota management,
per-user serialisation, caching, and exponential-backoff retry.
"""

import json
import asyncio
import time
import logging
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import google.generativeai as genai

from app.core.config import settings
from app.core.supabase import get_supabase
from app.services.ai_quota_manager import quota_manager, retry_strategy

logger = logging.getLogger(__name__)


class AIService:
    """
    Single, canonical AI service.

    Key design decisions:
    - Per-user asyncio.Semaphore(1): only one Gemini call per user at a time,
      regardless of how many browser tabs or concurrent requests exist.
    - Server-side 2-second inter-call delay: enforced inside every
      _generate_*_internal() method via _enforce_rate_limit().
    - 24-hour Supabase cache: identical prompts return instantly without
      consuming any Gemini quota.
    - Quota tracking delegated entirely to QuotaManager (no duplicate checks).
    """

    _CACHE_TTL_SECONDS = 86_400   # 24 hours
    _MIN_CALL_INTERVAL = 2.0      # seconds between consecutive Gemini calls

    def __init__(self):
        self.supabase = get_supabase()
        self._last_call: float = 0.0          # monotonic timestamp of last Gemini call
        self._user_semaphores: Dict[str, asyncio.Semaphore] = {}  # per-user lock

        # ── Gemini ────────────────────────────────────────────────────────────
        self.gemini_model = None
        self.gemini_model_name = "unknown"
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model, self.gemini_model_name = self._init_gemini_model()

        # ── OpenAI (optional fallback) ────────────────────────────────────────
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI fallback client initialised")
            except Exception as exc:
                logger.warning(f"OpenAI init failed (fallback unavailable): {exc}")

    # ─────────────────────────────────────────────────────────────────────────
    # INITIALISATION HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _init_gemini_model(self):
        """Try models in preference order; return (model, name) or (None, 'none')."""
        for name in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"):
            try:
                model = genai.GenerativeModel(name)
                logger.info(f"Gemini model initialised: {name}")
                return model, name
            except Exception as exc:
                logger.warning(f"Could not init {name}: {exc}")
        logger.error("No Gemini model could be initialised")
        return None, "none"

    def _get_user_semaphore(self, user_id: str) -> asyncio.Semaphore:
        """
        Return (creating if needed) a per-user Semaphore(1).
        This serialises all Gemini calls for a single user so that
        even if the frontend fires two requests simultaneously, they
        queue rather than race.
        """
        if user_id not in self._user_semaphores:
            self._user_semaphores[user_id] = asyncio.Semaphore(1)
        return self._user_semaphores[user_id]

    # ─────────────────────────────────────────────────────────────────────────
    # RATE LIMITING
    # ─────────────────────────────────────────────────────────────────────────

    async def _enforce_rate_limit(self):
        """
        Ensure at least _MIN_CALL_INTERVAL seconds between consecutive
        Gemini API calls (global, not per-user — the API limit is global).
        """
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._MIN_CALL_INTERVAL:
            wait = self._MIN_CALL_INTERVAL - elapsed
            logger.debug(f"Rate-limit pause: {wait:.2f}s")
            await asyncio.sleep(wait)
        self._last_call = time.monotonic()

    # ─────────────────────────────────────────────────────────────────────────
    # CACHE HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _hash_prompt(self, **kwargs) -> str:
        """Deterministic SHA-256 hash of prompt parameters."""
        return hashlib.sha256(
            json.dumps(kwargs, sort_keys=True).encode()
        ).hexdigest()

    async def _get_cached(self, user_id: str, content_type: str, prompt_hash: str) -> Optional[Dict]:
        """Return cached result dict if it exists and is still fresh, else None."""
        try:
            resp = (
                self.supabase.table("ai_cache")
                .select("result, created_at")
                .eq("user_id", user_id)
                .eq("content_type", content_type)
                .eq("prompt_hash", prompt_hash)
                .execute()
            )
            if resp.data:
                entry = resp.data[0]
                # Handle both timezone-aware and naive ISO strings
                created_raw = entry["created_at"].replace("Z", "+00:00")
                created_at = datetime.fromisoformat(created_raw)
                # Compare as naive UTC
                age = datetime.utcnow() - created_at.replace(tzinfo=None)
                if age < timedelta(seconds=self._CACHE_TTL_SECONDS):
                    logger.info(f"Cache HIT  [{content_type}] user={user_id[:8]}…")
                    return json.loads(entry["result"])
                # Expired — delete silently
                self.supabase.table("ai_cache").delete().eq("user_id", user_id).eq(
                    "content_type", content_type
                ).eq("prompt_hash", prompt_hash).execute()
        except Exception as exc:
            logger.warning(f"Cache read error: {exc}")
        return None

    async def _set_cached(self, user_id: str, content_type: str, prompt_hash: str, result: Dict):
        """Write result to cache; silently ignore errors."""
        try:
            self.supabase.table("ai_cache").upsert(
                {
                    "user_id": user_id,
                    "content_type": content_type,
                    "prompt_hash": prompt_hash,
                    "result": json.dumps(result),
                    "created_at": datetime.utcnow().isoformat(),
                },
                on_conflict="user_id,content_type,prompt_hash",
            ).execute()
            logger.debug(f"Cache WRITE [{content_type}] user={user_id[:8]}…")
        except Exception as exc:
            logger.warning(f"Cache write error: {exc}")

    # ─────────────────────────────────────────────────────────────────────────
    # JSON EXTRACTION HELPER
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str, array: bool = False) -> Dict | list:
        """
        Extract the first JSON object or array from a Gemini response string.
        Raises ValueError if nothing parseable is found.
        """
        open_ch, close_ch = ("[", "]") if array else ("{", "}")
        start = text.find(open_ch)
        end = text.rfind(close_ch) + 1
        if start == -1 or end <= start:
            raise ValueError(f"No JSON {'array' if array else 'object'} found in response")
        return json.loads(text[start:end])

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API — TITLES
    # ─────────────────────────────────────────────────────────────────────────

    async def generate_titles(
        self,
        user_id: str,
        topic: str,
        keywords: List[str] = None,
        tone: str = "engaging",
        target_audience: Optional[str] = None,
        count: int = 5,
        use_cache: bool = True,
    ) -> Dict:
        """
        Generate optimised YouTube titles.
        Returns a plain dict:
          {"titles": [{"title": ..., "seo_score": ..., "reasoning": ...}], ...}
        """
        prompt_hash = self._hash_prompt(
            topic=topic, keywords=keywords, tone=tone,
            target_audience=target_audience, count=count
        )

        if use_cache:
            cached = await self._get_cached(user_id, "title", prompt_hash)
            if cached:
                return cached

        async with self._get_user_semaphore(user_id):
            result = await retry_strategy.execute_with_retry(
                self._titles_internal,
                topic, keywords, tone, target_audience, count,
                retryable_exceptions=(Exception,),
            )

        await self._set_cached(user_id, "title", prompt_hash, result)
        quota_manager.record_request(user_id, tokens_used=2000)
        return result

    async def _titles_internal(
        self,
        topic: str,
        keywords: List[str],
        tone: str,
        target_audience: str,
        count: int,
    ) -> Dict:
        if not self.gemini_model:
            raise RuntimeError("Gemini model not initialised — check GEMINI_API_KEY")

        await self._enforce_rate_limit()

        kw = ", ".join(keywords) if keywords else "none"
        prompt = f"""Generate {count} optimised YouTube video titles.

Topic: {topic}
Keywords: {kw}
Tone: {tone}
Target Audience: {target_audience or 'General'}

Rules:
- 50-60 characters each
- Include primary keyword naturally
- Compelling but not clickbait
- Include SEO score 0-100 and one-line reasoning

Return ONLY a JSON array, no markdown:
[{{"title": "...", "seo_score": 85, "reasoning": "..."}}]"""

        response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
        titles_data = self._extract_json(response.text, array=True)

        return {
            "titles": titles_data,
            "count": len(titles_data),
            "model": self.gemini_model_name,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API — DESCRIPTION
    # ─────────────────────────────────────────────────────────────────────────

    async def generate_description(
        self,
        user_id: str,
        topic: str,
        title: str = None,
        keywords: List[str] = None,
        tone: str = "engaging",
        target_audience: str = None,
        video_length: str = "medium",
        include_timestamps: bool = True,
        include_links: bool = True,
        include_cta: bool = True,
        use_cache: bool = True,
    ) -> Dict:
        """
        Generate an optimised YouTube description.
        Returns a plain dict:
          {"description": "...", "seo_tips": [...]}
        """
        prompt_hash = self._hash_prompt(
            topic=topic, title=title, keywords=keywords, tone=tone,
            target_audience=target_audience, video_length=video_length,
            include_timestamps=include_timestamps, include_cta=include_cta,
        )

        if use_cache:
            cached = await self._get_cached(user_id, "description", prompt_hash)
            if cached:
                return cached

        async with self._get_user_semaphore(user_id):
            result = await retry_strategy.execute_with_retry(
                self._description_internal,
                topic, title, keywords, tone, target_audience,
                video_length, include_timestamps, include_links, include_cta,
                retryable_exceptions=(Exception,),
            )

        await self._set_cached(user_id, "description", prompt_hash, result)
        quota_manager.record_request(user_id, tokens_used=3000)
        return result

    async def _description_internal(
        self,
        topic: str,
        title: str,
        keywords: List[str],
        tone: str,
        target_audience: str,
        video_length: str,
        include_timestamps: bool,
        include_links: bool,
        include_cta: bool,
    ) -> Dict:
        if not self.gemini_model:
            raise RuntimeError("Gemini model not initialised — check GEMINI_API_KEY")

        await self._enforce_rate_limit()

        kw = ", ".join(keywords) if keywords else "none"
        extras = []
        if include_timestamps:
            extras.append("timestamp placeholders (e.g. 0:00 Intro)")
        if include_links:
            extras.append("link placeholders")
        if include_cta:
            extras.append("subscribe/like call-to-action")
        extras_str = ", ".join(extras) or "basic structure"

        prompt = f"""Generate an optimised YouTube video description.

Topic: {topic}
Title: {title or 'Not provided'}
Keywords: {kw}
Tone: {tone}
Target Audience: {target_audience or 'General'}
Video Length: {video_length}
Include: {extras_str}

Rules:
- First line: compelling hook (50-100 chars)
- Weave in keywords naturally
- Scannable with line breaks
- 3-5 actionable SEO tips at the end

Return ONLY a JSON object, no markdown:
{{"description": "...", "seo_tips": ["tip1", "tip2"]}}"""

        response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
        data = self._extract_json(response.text, array=False)

        return {
            "description": data.get("description", ""),
            "seo_tips": data.get("seo_tips") or [],
            "model": self.gemini_model_name,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API — TAGS
    # ─────────────────────────────────────────────────────────────────────────

    async def generate_tags(
        self,
        user_id: str,
        topic: str,
        title: str = None,
        keywords: List[str] = None,
        count: int = 20,
        use_cache: bool = True,
    ) -> Dict:
        """
        Generate optimised YouTube tags.
        Returns a plain dict:
          {"all_tags": [...], "primary_tags": [...], ...}
        """
        prompt_hash = self._hash_prompt(
            topic=topic, title=title, keywords=keywords, count=count
        )

        if use_cache:
            cached = await self._get_cached(user_id, "tags", prompt_hash)
            if cached:
                return cached

        async with self._get_user_semaphore(user_id):
            result = await retry_strategy.execute_with_retry(
                self._tags_internal,
                topic, title, keywords, count,
                retryable_exceptions=(Exception,),
            )

        await self._set_cached(user_id, "tags", prompt_hash, result)
        quota_manager.record_request(user_id, tokens_used=1500)
        return result

    async def _tags_internal(
        self,
        topic: str,
        title: str,
        keywords: List[str],
        count: int,
    ) -> Dict:
        if not self.gemini_model:
            raise RuntimeError("Gemini model not initialised — check GEMINI_API_KEY")

        await self._enforce_rate_limit()

        kw = ", ".join(keywords) if keywords else "none"
        prompt = f"""Generate {count} optimised YouTube tags.

Topic: {topic}
Title: {title or 'Not provided'}
Keywords: {kw}

Categorise into:
- primary_tags (3-5): core topic tags
- secondary_tags (5-7): related topic tags
- long_tail_tags (5-7): specific phrase tags
- broad_tags (3-5): general category tags

Rules:
- 1-3 words each
- No duplicates
- Maximise searchability

Return ONLY a JSON object, no markdown:
{{"primary_tags": [], "secondary_tags": [], "long_tail_tags": [], "broad_tags": [], "all_tags": []}}"""

        response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
        data = self._extract_json(response.text, array=False)

        all_tags = data.get("all_tags") or []
        return {
            "primary_tags":   data.get("primary_tags")   or [],
            "secondary_tags": data.get("secondary_tags") or [],
            "long_tail_tags": data.get("long_tail_tags") or [],
            "broad_tags":     data.get("broad_tags")     or [],
            "all_tags":       all_tags,
            "count":          len(all_tags),
            "model":          self.gemini_model_name,
            "generated_at":   datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # QUOTA INFO
    # ─────────────────────────────────────────────────────────────────────────

    def get_quota_info(self, user_id: str) -> Dict:
        """Delegate to QuotaManager."""
        return quota_manager.get_quota_info(user_id)


# ── Singleton ─────────────────────────────────────────────────────────────────
ai_service = AIService()
