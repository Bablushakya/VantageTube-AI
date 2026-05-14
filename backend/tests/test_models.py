"""
VantageTube AI - Pydantic Model Validation Tests
Covers all request/response models in app/models/
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.user import UserCreate, UserLogin, UserUpdate, PasswordChange, UserResponse, Token
from app.models.content import (
    TitleGenerationRequest, DescriptionGenerationRequest,
    TagsGenerationRequest, ThumbnailTextRequest, ThumbnailGenerationRequest,
    GeneratedTitle, GeneratedTitles, GeneratedDescription, GeneratedTags,
    VideoAnalysisRequest, VideoAnalysisResponse,
)
from app.models.settings import UserSettingsUpdate, UserSettingsResponse
from app.models.youtube import YouTubeChannelResponse, VideoResponse
from app.models.seo import VideoAnalysisRequest as SEOVideoAnalysisRequest
from app.models.seo import VideoAnalysisResponse as SEOVideoAnalysisResponse


# ── User Model Tests ─────────────────────────────────────────────────────────


class TestUserCreate:
    """2.1-2.4: UserCreate model validation."""

    def test_valid_user_create(self):
        """2.1: Valid data passes validation."""
        user = UserCreate(
            email="test@example.com",
            password="SecureP@ss1",
            confirm_password="SecureP@ss1",
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        # Model does NOT auto-generate display_name from first+last
        # It stays None unless explicitly provided

    def test_invalid_email(self):
        """2.2: Invalid email raises ValidationError."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="SecureP@ss1",
                confirm_password="SecureP@ss1",
            )

    def test_invalid_email_no_at(self):
        """2.2: Missing @ in email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="userexample.com",
                password="SecureP@ss1",
                confirm_password="SecureP@ss1",
            )

    def test_short_password(self):
        """2.3: Password < 8 chars raises ValidationError."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="Short1",
                confirm_password="Short1",
            )

    def test_model_does_not_check_confirm_match(self):
        """2.4: Model allows mismatched confirm_password (API enforces it)."""
        user = UserCreate(
            email="test@example.com",
            password="LongEnoughP@ss1",
            confirm_password="DifferentPassword1!",
        )
        assert user.password == "LongEnoughP@ss1"
        assert user.confirm_password == "DifferentPassword1!"

    def test_display_name_default(self):
        """display_name stays None unless explicitly set by the API layer."""
        user = UserCreate(
            email="test@example.com",
            password="SecureP@ss1",
            confirm_password="SecureP@ss1",
            first_name="Jane",
            last_name="Smith",
        )
        # The pydantic model does not auto-compute display_name
        # The API layer handles this logic
        assert user.display_name is None

    def test_display_name_custom(self):
        """Custom display_name overrides default."""
        user = UserCreate(
            email="test@example.com",
            password="SecureP@ss1",
            confirm_password="SecureP@ss1",
            display_name="JaneS",
        )
        assert user.display_name == "JaneS"


class TestUserLogin:
    """2.5: UserLogin model validation."""

    def test_valid_login(self):
        """2.5: Valid email/password."""
        login = UserLogin(email="test@example.com", password="MyPassword1!")
        assert login.email == "test@example.com"
        assert login.password == "MyPassword1!"

    def test_login_invalid_email(self):
        """Invalid email raises error."""
        with pytest.raises(ValidationError):
            UserLogin(email="bad", password="MyPassword1!")


class TestUserUpdate:
    """UserUpdate - partial updates."""

    def test_partial_update(self):
        """Only provided fields are set."""
        update = UserUpdate(first_name="NewName")
        assert update.first_name == "NewName"
        assert update.last_name is None
        assert update.display_name is None

    def test_empty_update(self):
        """Empty update is valid (no required fields)."""
        update = UserUpdate()
        assert update.first_name is None

    def test_update_all_fields(self):
        """All fields can be updated."""
        update = UserUpdate(
            first_name="A", last_name="B", display_name="C",
            username="username", country="us", niche="tech", bio="Hello"
        )
        assert update.username == "username"
        assert update.country == "us"
        assert update.niche == "tech"
        assert update.bio == "Hello"


class TestPasswordChange:
    """2.12: PasswordChange model validation."""

    def test_valid_password_change(self):
        """Valid password change."""
        pc = PasswordChange(
            current_password="OldP@ss1",
            new_password="NewP@ss123",
            confirm_password="NewP@ss123",
        )
        assert pc.new_password == "NewP@ss123"

    def test_short_new_password(self):
        """2.12: New password < 8 chars."""
        with pytest.raises(ValidationError):
            PasswordChange(
                current_password="OldP@ss1",
                new_password="Short1",
                confirm_password="Short1",
            )


# ── Content Model Tests ──────────────────────────────────────────────────────


class TestVideoAnalysisRequest:
    """2.6-2.8: VideoAnalysisRequest validation."""

    def test_default_values(self):
        """2.6: Default values correct."""
        req = VideoAnalysisRequest(topic="Python")
        assert req.count == 5
        assert req.tone == "engaging"
        assert req.keywords == []
        assert req.topic == "Python"

    def test_count_custom(self):
        """Custom count accepted."""
        req = VideoAnalysisRequest(topic="Python", count=3)
        assert req.count == 3

    def test_count_min_boundary(self):
        """2.7: count=1 is valid (minimum)."""
        req = VideoAnalysisRequest(topic="Python", count=1)
        assert req.count == 1

    def test_count_max_boundary(self):
        """2.7: count=10 is valid (maximum)."""
        req = VideoAnalysisRequest(topic="Python", count=10)
        assert req.count == 10

    def test_count_zero_invalid(self):
        """2.7: count=0 raises error."""
        with pytest.raises(ValidationError):
            VideoAnalysisRequest(topic="Python", count=0)

    def test_count_eleven_invalid(self):
        """2.7: count=11 raises error."""
        with pytest.raises(ValidationError):
            VideoAnalysisRequest(topic="Python", count=11)

    def test_empty_topic(self):
        """2.8: Empty topic is NOT validated at the model level (allow empty)."""
        # The model allows empty string - API layer should validate separately
        req = VideoAnalysisRequest(topic="")
        assert req.topic == ""

    def test_custom_tone(self):
        """Custom tone accepted."""
        req = VideoAnalysisRequest(topic="Python", tone="professional")
        assert req.tone == "professional"

    def test_with_keywords(self):
        """Keywords list accepted."""
        req = VideoAnalysisRequest(topic="Python", keywords=["python", "coding"])
        assert req.keywords == ["python", "coding"]


class TestTitleGenerationRequest:
    """2.9: TitleGenerationRequest validation."""

    def test_valid_request(self):
        """Valid request passes."""
        req = TitleGenerationRequest(topic="Python")
        assert req.count == 5

    def test_count_1_valid(self):
        """count=1 is valid."""
        req = TitleGenerationRequest(topic="Python", count=1)
        assert req.count == 1

    def test_count_10_valid(self):
        """count=10 is valid."""
        req = TitleGenerationRequest(topic="Python", count=10)
        assert req.count == 10

    def test_count_0_invalid(self):
        """count=0 invalid."""
        with pytest.raises(ValidationError):
            TitleGenerationRequest(topic="Python", count=0)

    def test_count_11_invalid(self):
        """count=11 invalid."""
        with pytest.raises(ValidationError):
            TitleGenerationRequest(topic="Python", count=11)


class TestTagsGenerationRequest:
    """2.10: TagsGenerationRequest validation."""

    def test_valid_request(self):
        """Valid request passes."""
        req = TagsGenerationRequest(topic="Python")
        assert req.count == 15

    def test_count_30_valid(self):
        """count=30 is valid boundary."""
        req = TagsGenerationRequest(topic="Python", count=30)
        assert req.count == 30

    def test_count_0_invalid(self):
        """count=0 invalid."""
        with pytest.raises(ValidationError):
            TagsGenerationRequest(topic="Python", count=0)

    def test_count_31_invalid(self):
        """count=31 invalid (over max)."""
        with pytest.raises(ValidationError):
            TagsGenerationRequest(topic="Python", count=31)


class TestGeneratedTitle:
    """2.15: GeneratedTitle score boundary."""

    def test_score_0_valid(self):
        """score=0 is valid minimum."""
        t = GeneratedTitle(text="Title", score=0, reasoning="OK")
        assert t.score == 0

    def test_score_100_valid(self):
        """score=100 is valid maximum."""
        t = GeneratedTitle(text="Title", score=100, reasoning="OK")
        assert t.score == 100

    def test_score_negative_invalid(self):
        """score=-1 raises error."""
        with pytest.raises(ValidationError):
            GeneratedTitle(text="Title", score=-1, reasoning="OK")

    def test_score_101_invalid(self):
        """score=101 raises error."""
        with pytest.raises(ValidationError):
            GeneratedTitle(text="Title", score=101, reasoning="OK")


class TestGeneratedTitles:
    """2.16: GeneratedTitles required fields."""

    def test_all_fields_present(self):
        """2.16: Required fields present."""
        gt = GeneratedTitles(
            titles=[GeneratedTitle(text="T1", score=80, reasoning="Good")],
            topic="Python",
            keywords=[],
            generated_at=datetime.utcnow(),
        )
        assert gt.topic == "Python"
        assert gt.keywords == []
        assert len(gt.titles) == 1
        assert gt.titles[0].text == "T1"


class TestGeneratedDescription:
    """2.17: GeneratedDescription word_count."""

    def test_word_count_calculation(self):
        """2.17: word_count matches description length."""
        desc = "This is a sample description with eight words now"
        gd = GeneratedDescription(
            description=desc,
            word_count=len(desc.split()),
            includes_timestamps=True,
            includes_links=True,
            includes_cta=True,
            seo_tips=["tip1"],
            generated_at=datetime.utcnow(),
        )
        assert gd.word_count == len(desc.split())


class TestVideoAnalysisResponse:
    """2.18: VideoAnalysisResponse full shape."""

    def test_all_fields_present(self):
        """2.18: All 6 fields present."""
        resp = VideoAnalysisResponse(
            titles=GeneratedTitles(titles=[], topic="T", keywords=[], generated_at=datetime.utcnow()),
            description=GeneratedDescription(
                description="", word_count=0,
                includes_timestamps=True, includes_links=True, includes_cta=True,
                seo_tips=[], generated_at=datetime.utcnow()
            ),
            tags=GeneratedTags(tags=[], tag_count=0, tag_categories={}, generated_at=datetime.utcnow()),
            cache_hit=False,
            gemini_calls_made=1,
            generated_at=datetime.utcnow(),
        )
        assert resp.cache_hit is False
        assert resp.gemini_calls_made == 1


# ── Settings Model Tests ─────────────────────────────────────────────────────


class TestUserSettingsUpdate:
    """2.11: UserSettingsUpdate theme validation."""

    def test_theme_dark_valid(self):
        """'dark' is valid theme."""
        s = UserSettingsUpdate(theme="dark")
        assert s.theme == "dark"

    def test_theme_light_valid(self):
        """'light' is valid theme."""
        s = UserSettingsUpdate(theme="light")
        assert s.theme == "light"

    def test_theme_rejects_invalid(self):
        """2.11: Invalid theme raises ValidationError."""
        with pytest.raises(ValidationError):
            UserSettingsUpdate(theme="red")

    def test_partial_settings_update(self):
        """Only provided fields are set, others use defaults."""
        s = UserSettingsUpdate(email_notifications=True)
        assert s.email_notifications is True
        # Other fields have defaults, not None
        assert s.theme == "dark"  # default value

    def test_all_fields(self):
        """All settings fields accepted."""
        s = UserSettingsUpdate(
            theme="dark", accent_color="#FF0000", font_size="large",
            compact_mode=True, email_notifications=True, weekly_seo_report=True,
            trending_alerts=True, feature_updates=True, milestone_alerts=True,
            profile_visibility=True, analytics_sharing=False,
        )
        assert s.accent_color == "#FF0000"
        assert s.font_size == "large"
        assert s.compact_mode is True


# ── SEO Model Tests ──────────────────────────────────────────────────────────


class TestSEOVideoAnalysisRequest:
    """2.13: SEO analysis request."""

    def test_valid_request(self):
        """Valid request."""
        req = SEOVideoAnalysisRequest(video_id="video-123")
        assert req.video_id == "video-123"
        assert req.force_reanalysis is False

    def test_force_reanalysis_true(self):
        """force_reanalysis can be set."""
        req = SEOVideoAnalysisRequest(video_id="v1", force_reanalysis=True)
        assert req.force_reanalysis is True

    def test_empty_video_id(self):
        """Empty video_id is allowed (no min_length validation)."""
        req = SEOVideoAnalysisRequest(video_id="")
        assert req.video_id == ""


class TestUserResponse:
    """UserResponse serialization."""

    def test_user_response_fields(self):
        """UserResponse has all required fields."""
        resp = UserResponse(
            id="user-1",
            email="test@test.com",
            first_name="John",
            last_name="Doe",
            display_name="John Doe",
            plan="free",
            created_at=datetime.utcnow(),
        )
        assert resp.id == "user-1"
        assert resp.plan == "free"
        assert resp.email == "test@test.com"


class TestToken:
    """Token response model."""

    def test_token_fields(self):
        """Token has access_token, refresh_token, token_type, user."""
        user = UserResponse(id="u1", email="t@t.com", display_name="Test", plan="free", created_at=datetime.utcnow())
        token = Token(
            access_token="abc",
            refresh_token="def",
            token_type="bearer",
            user=user,
        )
        assert token.access_token == "abc"
        assert token.token_type == "bearer"


# ── YouTube Model Tests ──────────────────────────────────────────────────────


class TestYouTubeChannelResponse:
    """YouTubeChannelResponse fields."""

    def test_channel_fields(self):
        """Channel response has required fields."""
        resp = YouTubeChannelResponse(
            id="ch-1",
            user_id="user-1",
            channel_id="UC123",
            channel_name="My Channel",
            subscriber_count=1000,
            video_count=50,
            view_count=50000,
            is_connected=True,
            connected_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        assert resp.channel_name == "My Channel"
        assert resp.subscriber_count == 1000
        assert resp.is_connected is True
        assert resp.user_id == "user-1"
