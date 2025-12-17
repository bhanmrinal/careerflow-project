"""Tests for LLM-based intent routing."""

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
    for pdf in PROJECT_ROOT.glob("*.pdf"):
        if "assignment" not in pdf.name.lower():
            return pdf
    return None


def test_routing():
    """Test LLM-based routing with various edge cases."""
    resume_path = get_resume_path()
    if not resume_path:
        print("No resume file found. Skipping test.")
        return

    # Upload resume
    print("=== UPLOADING RESUME ===")
    with open(resume_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/resume/upload",
            files={"file": (resume_path.name, f, "application/pdf")},
        )
        data = response.json()
        resume_id = data.get("resume_id")
        print(f"Resume ID: {resume_id}\n")

    if not resume_id:
        print("Failed to upload resume!")
        return

    # Test cases: (message, expected_agent)
    test_cases = [
        # Job Matching
        (
            "I want to apply for this role:\n\nRequirements:\n- 3+ years Python",
            "job_matching",
        ),
        ("check how my resume scores against this posting", "job_matching"),
        # Company Research (any company name)
        ("optimize my resume for Stripe", "company_research"),
        ("I'm applying to Databricks, help me tailor my resume", "company_research"),
        ("make my resume better for Razorpay", "company_research"),
        # Translation
        ("convert my resume to Japanese for Tokyo job market", "translation"),
        ("I need this in Portuguese for Brazil", "translation"),
        ("adapt my CV for the UK market", "translation"),
        # Edge cases
        ("I have a JD from Acme Corp, match my skills", "job_matching"),
        ("translate for German companies", "translation"),
    ]

    print("=== TESTING LLM-BASED ROUTING ===\n")

    results = []
    for message, expected in test_cases:
        print(f"Message: {message[:50]}...")
        print(f"Expected: {expected}")

        response = requests.post(
            f"{BASE_URL}/chat/message",
            json={"message": message, "resume_id": resume_id},
            timeout=120,
        )
        data = response.json()
        actual = data.get("agent_type", "unknown")

        match = "✅" if actual == expected else "❌"
        print(f"Actual: {actual} {match}")
        print("-" * 50)

        results.append((message[:40], expected, actual, actual == expected))

    # Summary
    print("\n=== SUMMARY ===")
    passed = sum(1 for r in results if r[3])
    print(f"Passed: {passed}/{len(results)}")

    if passed < len(results):
        print("\nFailed cases:")
        for msg, exp, act, success in results:
            if not success:
                print(f"  - '{msg}...' expected {exp}, got {act}")


if __name__ == "__main__":
    test_routing()
