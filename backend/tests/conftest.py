"""
Shared test fixtures for VantageTube AI backend tests.
"""

import os
import sys
from pathlib import Path
from typing import Dict

import pytest
from fastapi.testclient import TestClient

# Ensure the .env is loaded before importing app modules
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path, override=False)

from app.main import app
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Generate valid JWT Authorization headers for a test user."""
    token = create_access_token({"sub": "test-user-id-12345", "email": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin() -> Dict[str, str]:
    """Generate valid JWT Authorization headers for an admin test user."""
    token = create_access_token({"sub": "admin-user-id-67890", "email": "admin@example.com"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_auth_headers() -> Dict[str, str]:
    """Generate an expired JWT token for testing auth failure."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.core.config import settings
    expire = datetime.now(timezone.utc) - timedelta(hours=1)
    payload = {
        "sub": "test-user-id-12345",
        "email": "test@example.com",
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def invalid_auth_headers() -> Dict[str, str]:
    """Invalid/malformed token."""
    return {"Authorization": "Bearer this-is-definitely-not-a-valid-jwt-token"}


@pytest.fixture
def sample_topic() -> str:
    """A sample video topic for content generation tests."""
    return "How to learn Python programming in 2024"


@pytest.fixture
def sample_keywords() -> list:
    """Sample SEO keywords."""
    return ["python", "programming", "beginner tutorial"]


@pytest.fixture
def mock_supabase(monkeypatch):
    """Mock Supabase client to avoid requiring a real database connection."""
    from unittest.mock import MagicMock, AsyncMock

    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = [{"id": "mock-id"}]
    mock.table.return_value.update.return_value.execute.return_value.data = [{"id": "mock-id"}]
    mock.table.return_value.delete.return_value.execute.return_value.data = [{"id": "mock-id"}]

    def mock_get_supabase():
        return mock

    monkeypatch.setattr("app.core.supabase.get_supabase", mock_get_supabase)
    return mock


# ── Password helpers for direct testing ──────────────────────────────────────


@pytest.fixture
def password_hasher():
    """Provide password hashing utilities."""
    return {
        "hash": get_password_hash,
        "verify": verify_password,
    }