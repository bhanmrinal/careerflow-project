"""
Pytest configuration and shared fixtures.
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# API base URL for integration tests
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")


@pytest.fixture
def api_url():
    """Return the API base URL."""
    return API_BASE_URL


@pytest.fixture
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT


@pytest.fixture
def sample_resume_path(project_root):
    """Return path to sample resume if exists."""
    resume_path = project_root / "Resume_Mrinal_Bhan.pdf"
    if resume_path.exists():
        return resume_path
    return None
