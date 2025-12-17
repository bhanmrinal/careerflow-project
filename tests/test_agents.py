"""Integration tests for all three AI agents."""

import sys
from pathlib import Path

import requests

# Force UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000/api"
PROJECT_ROOT = Path(__file__).parent.parent


def get_resume_path():
    """Get path to test resume."""
    resume_path = PROJECT_ROOT / "Resume_Mrinal_Bhan.pdf"
    if resume_path.exists():
        return resume_path
    # Fallback to any PDF in project root
    for pdf in PROJECT_ROOT.glob("*.pdf"):
        if "assignment" not in pdf.name.lower():
            return pdf
    return None


def test_all_agents():
    """Test all three agents with a real resume."""
    resume_path = get_resume_path()
    if not resume_path:
        print("No resume file found. Skipping test.")
        return

    # Upload resume
    print("=" * 60)
    print("UPLOADING RESUME")
    print("=" * 60)
    with open(resume_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/resume/upload",
            files={"file": (resume_path.name, f, "application/pdf")},
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Resume ID: {data.get('resume_id')}")
        print(f"Sections Found: {data.get('sections_detected')}")
        resume_id = data.get("resume_id")

    if not resume_id:
        print("Failed to upload resume!")
        return

    # Test Company Research Agent
    print("\n" + "=" * 60)
    print("TEST 1: COMPANY RESEARCH & OPTIMIZATION AGENT")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/chat/message",
        json={
            "message": "Optimize my resume for Google. I want to apply for an ML Engineer position.",
            "resume_id": resume_id,
        },
        timeout=120,
    )
    data = response.json()
    print(f"Agent Used: {data.get('agent_type')}")
    print(f"Version: v{data.get('current_resume_version')}")
    print(f"Changes: {len(data.get('resume_changes', []))}")
    assert data.get("agent_type") == "company_research"

    conv_id = data.get("conversation_id")

    # Test Job Matching Agent
    print("\n" + "=" * 60)
    print("TEST 2: JOB DESCRIPTION MATCHING AGENT")
    print("=" * 60)

    job_description = """
    ML Engineer - Partnership Track
    Requirements:
    - 2+ years of experience in ML/AI
    - Strong Python skills
    - Experience with LLMs and RAG
    """

    response = requests.post(
        f"{BASE_URL}/chat/message",
        json={
            "message": f"Match my resume to this job:\n\n{job_description}",
            "resume_id": resume_id,
            "conversation_id": conv_id,
        },
        timeout=120,
    )
    data = response.json()
    print(f"Agent Used: {data.get('agent_type')}")
    print(f"Version: v{data.get('current_resume_version')}")
    assert data.get("agent_type") == "job_matching"

    # Test Translation Agent
    print("\n" + "=" * 60)
    print("TEST 3: TRANSLATION & LOCALIZATION AGENT")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/chat/message",
        json={
            "message": "Translate my resume to German for the German job market.",
            "resume_id": resume_id,
            "conversation_id": conv_id,
        },
        timeout=120,
    )
    data = response.json()
    print(f"Agent Used: {data.get('agent_type')}")
    print(f"Version: v{data.get('current_resume_version')}")
    assert data.get("agent_type") == "translation"

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_all_agents()
