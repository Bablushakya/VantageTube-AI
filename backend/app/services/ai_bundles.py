"""
VantageTube AI - Bundle Factory Functions
==========================================
Pre-built TaskBundle constructors for each platform feature.

Each factory returns a TaskBundle ready to pass to:
    result = await ai_orchestrator.submit_bundle(user_id, bundle)

Adding a new platform feature's AI workflow = define a new factory here.
The AIOrchestrator core never needs to change.

Token estimates (used for quota pre-check):
    titles      → 1,500
    description → 2,000
    tags        → 1,000
    hook        →   800
    outline     → 1,500
    cta         →   500
"""

from __future__ import annotations

from typing import List, Optional

from app.services.ai_orchestrator import AITask, TaskBundle


# ─────────────────────────────────────────────────────────────────────────────
# 9.1  VIDEO ANALYSIS BUNDLE
# ─────────────────────────────────────────────────────────────────────────────

def VideoAnalysisBundle(
    user_id:   str,
    topic:     str,
    keywords:  Optional[List[str]] = None,
    tone:      str = "engaging",
    count:     int = 5,
    video_id:  Optional[str] = None,
) -> TaskBundle:
    """
    Bundle for the Video SEO Analyzer feature.

    Combines three sub-tasks into a single Gemini call:
      1. titles      — {count} optimised YouTube titles with SEO scores
      2. description — full optimised description with SEO tips
      3. tags        — 20 categorised tags (primary, secondary, long-tail, broad)

    This replaces the old three-call sequential flow in analyzer.js,
    reducing Gemini API usage by 66% for the most common user action.

    Args:
        user_id:  Authenticated user's ID.
        topic:    Video topic / title (used as the generation seed).
        keywords: Target SEO keywords (optional).
        tone:     Content tone — "engaging", "professional", "educational", etc.
        count:    Number of title options to generate (1-10, default 5).
        video_id: Database video ID for history tracking (optional).

    Returns:
        TaskBundle with bundle_type="video_analysis" and three AITask entries.

    Token estimate: 1500 + 2000 + 1000 = 4500 tokens per call.
    """
    kw = keywords or []

    tasks = [
        AITask(
            task_type="titles",
            prompt_params={
                "topic":    topic,
                "keywords": kw,
                "tone":     tone,
                "count":    count,
            },
            estimated_tokens=1_500,
        ),
        AITask(
            task_type="description",
            prompt_params={
                "topic":    topic,
                "keywords": kw,
                "tone":     tone,
            },
            estimated_tokens=2_000,
        ),
        AITask(
            task_type="tags",
            prompt_params={
                "topic":      topic,
                "keywords":   kw,
                "count_tags": 20,
            },
            estimated_tokens=1_000,
        ),
    ]

    return TaskBundle(
        bundle_type="video_analysis",
        user_id=user_id,
        tasks=tasks,
        cache_ttl=86_400,   # 24 hours
    )


# ─────────────────────────────────────────────────────────────────────────────
# 9.2  GENERATOR BUNDLE
# ─────────────────────────────────────────────────────────────────────────────

def GeneratorBundle(
    user_id:  str,
    topic:    str,
    keywords: Optional[List[str]] = None,
    tone:     str = "engaging",
) -> TaskBundle:
    """
    Bundle for the AI Generator feature.

    Combines three sub-tasks into a single Gemini call:
      1. hook    — attention-grabbing opening hook for the video
      2. outline — structured content outline with sections
      3. cta     — call-to-action text for end screen / description

    Args:
        user_id:  Authenticated user's ID.
        topic:    Video topic.
        keywords: Target SEO keywords (optional).
        tone:     Content tone.

    Returns:
        TaskBundle with bundle_type="generator" and three AITask entries.

    Token estimate: 800 + 1500 + 500 = 2800 tokens per call.
    """
    kw = keywords or []

    tasks = [
        AITask(
            task_type="hook",
            prompt_params={
                "topic":    topic,
                "keywords": kw,
                "tone":     tone,
            },
            estimated_tokens=800,
        ),
        AITask(
            task_type="outline",
            prompt_params={
                "topic":    topic,
                "keywords": kw,
                "tone":     tone,
            },
            estimated_tokens=1_500,
        ),
        AITask(
            task_type="cta",
            prompt_params={
                "topic": topic,
                "tone":  tone,
            },
            estimated_tokens=500,
        ),
    ]

    return TaskBundle(
        bundle_type="generator",
        user_id=user_id,
        tasks=tasks,
        cache_ttl=86_400,   # 24 hours
    )
