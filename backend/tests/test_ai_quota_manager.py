"""
VantageTube AI - AI Quota Manager Tests
Covers: quota_manager.py - quota checking, recording, reset, retry strategy
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_quota_manager import (
    quota_manager,
    QuotaStatus,
    QuotaManager,
    RetryStrategy,
)


class TestQuotaManager:
    """3.11-3.16: QuotaManager checks, records, and tracks usage."""

    @pytest.fixture(autouse=True)
    def reset_quota(self):
        """Reset quota manager state before each test."""
        # Clear the L1 cache between tests
        with patch.object(quota_manager, "_get_usage", return_value={
            "minute": 0, "hour": 0, "day": 0,
            "tokens_minute": 0, "tokens_day": 0,
        }):
            yield

    @patch.object(QuotaManager, "_get_usage", return_value={
        "minute": 0, "hour": 0, "day": 0,
        "tokens_minute": 0, "tokens_day": 0,
    })
    def test_check_quota_available(self, mock_usage):
        """3.11: Fresh user has AVAILABLE quota."""
        qm = QuotaManager(tier="free")
        status, msg = asyncio.run(qm.check_quota("user-1", 1000))
        assert status == QuotaStatus.AVAILABLE
        assert msg == "Quota available"

    @patch.object(QuotaManager, "_get_usage", return_value={
        "minute": 10, "hour": 50, "day": 100,
        "tokens_minute": 5000, "tokens_day": 50000,
    })
    def test_get_quota_info_shape(self, mock_usage):
        """3.16: get_quota_info returns correct stats structure."""
        qm = QuotaManager(tier="free")
        info = qm.get_quota_info("user-1")
        assert "tier" in info
        assert "requests" in info
        assert "tokens" in info
        assert info["requests"]["used_minute"] == 10
        assert info["tokens"]["used_day"] == 50000

    @patch.object(QuotaManager, "_get_usage", return_value={
        "minute": 0, "hour": 0, "day": 0,
        "tokens_minute": 0, "tokens_day": 0,
    })
    def test_unknown_user_returns_zero_usage(self, mock_usage):
        """User with no requests has zero usage."""
        qm = QuotaManager(tier="free")
        info = qm.get_quota_info("never-used-user")
        assert info["requests"]["used_minute"] == 0
        assert info["requests"]["used_day"] == 0

    @patch.object(QuotaManager, "_get_usage", return_value={
        "minute": 14, "hour": 100, "day": 500,
        "tokens_minute": 10000, "tokens_day": 100000,
    })
    def test_near_minute_limit_returns_available(self, mock_usage):
        """When below per-minute request limit, status is AVAILABLE."""
        qm = QuotaManager(tier="free")
        status, msg = asyncio.run(qm.check_quota("user-1", 500))
        assert status == QuotaStatus.AVAILABLE

    @patch.object(QuotaManager, "_get_usage", return_value={
        "minute": 0, "hour": 0, "day": 1499,
        "tokens_minute": 0, "tokens_day": 1000,
    })
    def test_daily_limit_near_boundary(self, mock_usage):
        """Daily request limit at 1499 out of 1500 - should still be AVAILABLE."""
        qm = QuotaManager(tier="free")
        status, msg = asyncio.run(qm.check_quota("user-1", 1))  # only 1 token more
        assert status == QuotaStatus.AVAILABLE

    @patch.object(QuotaManager, "_get_usage", return_value={
        "minute": 0, "hour": 0, "day": 0,
        "tokens_minute": 0, "tokens_day": 499000,
    })
    def test_daily_token_limit_exceeded(self, mock_usage):
        """When near daily token limit (499K/500K), tokens for request push it over."""
        qm = QuotaManager(tier="free")
        # tokens_per_day = 500000, used = 499000, request needs 2000 = total 501000 > 500000
        status, msg = asyncio.run(qm.check_quota("user-1", 2000))
        assert status == QuotaStatus.EXHAUSTED
        assert "Daily token limit" in msg

    @patch.object(QuotaManager, "_get_usage", return_value={
        "minute": 0, "hour": 0, "day": 0,
        "tokens_minute": 30000, "tokens_day": 10000,
    })
    def test_per_minute_token_limit(self, mock_usage):
        """When per-minute token limit exceeded (30K + 3K > 32K)."""
        qm = QuotaManager(tier="free")
        status, msg = asyncio.run(qm.check_quota("user-1", 3000))
        assert status == QuotaStatus.LIMITED
        assert "Token rate limit" in msg


class TestRetryStrategy:
    """3.17-3.18: RetryStrategy exponential backoff."""

    def test_successful_first_attempt(self):
        """Strategy returns result of successful first attempt."""
        strategy = RetryStrategy(max_retries=3, initial_delay=0.01)

        async def succeed():
            return "success"

        result = asyncio.run(strategy.execute_with_retry(succeed))
        assert result == "success"

    def test_retry_on_failure(self):
        """Strategy retries on transient failure."""
        strategy = RetryStrategy(max_retries=3, initial_delay=0.01)
        call_count = {"n": 0}

        async def fail_then_succeed():
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ValueError("Transient error")
            return "success"

        result = asyncio.run(strategy.execute_with_retry(fail_then_succeed))
        assert result == "success"
        assert call_count["n"] == 2

    def test_max_retries_exceeded(self):
        """3.17: Strategy raises after exceeding max_retries."""
        strategy = RetryStrategy(max_retries=2, initial_delay=0.01)

        async def always_fail():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            asyncio.run(strategy.execute_with_retry(always_fail))

    def test_exponential_backoff_increases_delay(self):
        """3.18: Each retry waits longer than the previous."""
        strategy = RetryStrategy(max_retries=3, initial_delay=0.01)
        delays = []
        call_count = {"n": 0}

        original_sleep = asyncio.sleep

        async def tracking_sleep(delay):
            delays.append(delay)
            await original_sleep(delay)

        async def always_fail():
            call_count["n"] += 1
            raise ValueError("Fail")

        with patch("asyncio.sleep", tracking_sleep):
            with pytest.raises(ValueError):
                asyncio.run(strategy.execute_with_retry(always_fail))

        # Delays should be increasing: base, base*2, base*4
        assert len(delays) == 3
        assert delays[0] < delays[1] < delays[2]

    def test_non_retryable_exception_not_retried(self):
        """Non-retryable exceptions are not retried."""
        strategy = RetryStrategy(max_retries=3, initial_delay=0.01)
        call_count = {"n": 0}

        async def fail_with_non_retryable():
            call_count["n"] += 1
            raise RuntimeError("Non-retryable")

        # execute_with_retry doesn't have non_retryable_exceptions parameter
        # It uses retryable_exceptions to define what IS retryable
        with pytest.raises(RuntimeError):
            asyncio.run(
                strategy.execute_with_retry(
                    fail_with_non_retryable,
                    # TypeError means this exception type won't match retryable_exceptions
                    retryable_exceptions=(ValueError, ConnectionError),
                )
            )

        # Should only be called once because RuntimeError is not in retryable_exceptions
        assert call_count["n"] == 1

    def test_success_after_multiple_retries(self):
        """Strategy can succeed after several retries."""
        strategy = RetryStrategy(max_retries=5, initial_delay=0.01)
        call_count = {"n": 0}

        async def succeed_on_third():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ConnectionError("Transient")
            return "ok"

        result = asyncio.run(strategy.execute_with_retry(succeed_on_third))
        assert result == "ok"
        assert call_count["n"] == 3