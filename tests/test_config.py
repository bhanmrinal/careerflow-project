"""Tests for configuration module."""

from app.core.config import Settings


def test_settings_defaults():
    """Test that default settings are loaded correctly."""
    settings = Settings()

    assert settings.app_name == "Careerflow Resume Optimizer"
    assert settings.groq_model == "llama-3.3-70b-versatile"
    assert settings.port == 8000


def test_firebase_credentials_none_when_incomplete():
    """Test that Firebase credentials return None when incomplete."""
    settings = Settings()

    # With no Firebase config, should return None
    if not settings.firebase_project_id:
        assert settings.firebase_credentials is None
