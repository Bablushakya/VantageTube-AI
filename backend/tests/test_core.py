"""
VantageTube AI - Core Configuration & Security Tests
Covers: config.py, security.py, supabase.py
"""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

from app.core.config import Settings, settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)


# ── Config Tests ─────────────────────────────────────────────────────────────


class TestSettings:
    """1.1-1.3: Configuration loading and defaults."""

    def test_settings_loaded(self):
        """1.1: Settings loaded from .env with correct types."""
        assert settings.APP_NAME == "VantageTube AI"
        assert settings.APP_VERSION == "1.0.0"
        assert isinstance(settings.DEBUG, bool)
        assert settings.ENVIRONMENT in ("development", "production", "testing")

    def test_cors_origins_parsing(self):
        """1.2: cors_origins property parses comma-separated string."""
        s = Settings(
            ALLOWED_ORIGINS="http://a.com,http://b.com,  http://c.com  ",
            SUPABASE_URL="http://test", SUPABASE_KEY="test",
            SUPABASE_SERVICE_KEY="test", SECRET_KEY="test",
        )
        origins = s.cors_origins
        assert len(origins) == 3
        assert origins == ["http://a.com", "http://b.com", "http://c.com"]

    def test_cors_origins_single_value(self):
        """1.2: Single origin returns single-item list."""
        s = Settings(
            ALLOWED_ORIGINS="http://localhost:3000",
            SUPABASE_URL="http://test", SUPABASE_KEY="test",
            SUPABASE_SERVICE_KEY="test", SECRET_KEY="test",
        )
        assert s.cors_origins == ["http://localhost:3000"]

    def test_cors_origins_empty(self):
        """1.2: Empty string returns list with empty string."""
        s = Settings(
            ALLOWED_ORIGINS="",
            SUPABASE_URL="http://test", SUPABASE_KEY="test",
            SUPABASE_SERVICE_KEY="test", SECRET_KEY="test",
        )
        assert s.cors_origins == [""]


# ── JWT Tests ────────────────────────────────────────────────────────────────


class TestJWTTokens:
    """1.4-1.7: JWT creation and validation."""

    def test_create_access_token_valid(self):
        """1.4: create_access_token generates a valid JWT."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)

        # Decode without verification to check structure
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_decode_access_token_valid(self):
        """1.5: decode_access_token returns payload for valid token."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"

    def test_decode_access_token_expired(self):
        """1.6: decode_access_token returns None for expired token."""
        token = create_access_token(
            {"sub": "user-123"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        # Wait a tiny bit to ensure expiry
        payload = decode_access_token(token)
        assert payload is None

    def test_decode_access_token_invalid_signature(self):
        """1.7: decode_access_token returns None for invalid signature."""
        # Create a token with a different key
        from app.core.config import settings as s
        token = jwt.encode(
            {"sub": "user-123", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong-secret-key-that-does-not-match",
            algorithm=s.ALGORITHM
        )
        payload = decode_access_token(token)
        assert payload is None

    def test_decode_access_token_malformed(self):
        """1.7: decode_access_token returns None for garbage token."""
        assert decode_access_token("not-a-jwt-token-at-all") is None

    def test_decode_access_token_empty(self):
        """1.7: decode_access_token returns None for empty string."""
        assert decode_access_token("") is None

    def test_create_refresh_token(self):
        """Refresh token creates valid JWT with longer expiry."""
        token = create_refresh_token({"sub": "user-123"})
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "user-123"
        assert "exp" in decoded

    def test_access_token_contains_email(self):
        """Access token preserves email claim."""
        token = create_access_token({"sub": "u1", "email": "user@example.com"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["email"] == "user@example.com"

    def test_access_token_default_expiry(self):
        """Access token has default 30-minute expiry."""
        token = create_access_token({"sub": "u1"})
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = decoded["exp"]
        # Should be ~30 minutes from now
        expected_min = datetime.utcnow() + timedelta(minutes=29)
        expected_max = datetime.utcnow() + timedelta(minutes=31)
        exp_dt = datetime.utcfromtimestamp(exp)
        assert expected_min < exp_dt < expected_max


# ── Password Hashing Tests ────────────────────────────────────────────────────


class TestPasswordHashing:
    """1.8-1.9: Password hashing and verification."""

    def test_password_hash_verify_roundtrip(self):
        """1.8: verify_password returns True for correct password."""
        plain = "MySecureP@ss123!"
        hashed = get_password_hash(plain)
        assert verify_password(plain, hashed) is True

    def test_password_hash_wrong_password(self):
        """1.9: verify_password returns False for incorrect password."""
        hashed = get_password_hash("CorrectPassword123!")
        assert verify_password("WrongPassword456!", hashed) is False

    def test_password_hash_different_each_time(self):
        """Each hash call produces a different hash (salt)."""
        plain = "SamePassword123!"
        h1 = get_password_hash(plain)
        h2 = get_password_hash(plain)
        assert h1 != h2  # bcrypt uses random salts
        assert verify_password(plain, h1) is True
        assert verify_password(plain, h2) is True

    def test_password_hash_empty_string(self):
        """Empty password can be hashed and verified."""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_password_hash_long_password(self):
        """Very long password (500 chars) can be hashed."""
        long_pw = "A" * 500
        hashed = get_password_hash(long_pw)
        assert verify_password(long_pw, hashed) is True