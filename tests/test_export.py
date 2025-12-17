"""Tests for resume export functionality."""

import sys
from pathlib import Path

import requests

# Force UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000/api"
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def get_resume_path():
    """Get path to test resume."""
    resume_path = PROJECT_ROOT / "Resume_Mrinal_Bhan.pdf"
    if resume_path.exists():
        return resume_path
    for pdf in PROJECT_ROOT.glob("*.pdf"):
        if "assignment" not in pdf.name.lower():
            return pdf
    return None


def test_export():
    """Test resume export in different formats."""
    resume_path = get_resume_path()
    if not resume_path:
        print("No resume file found. Skipping test.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Upload resume
    print("=== UPLOADING RESUME ===")
    with open(resume_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/resume/upload",
            files={"file": (resume_path.name, f, "application/pdf")},
        )
        data = response.json()
        print(f"Resume ID: {data.get('resume_id')}")
        resume_id = data.get("resume_id")

    if not resume_id:
        print("Failed to upload resume!")
        return

    # Optimize resume first
    print("\n=== OPTIMIZING RESUME ===")
    response = requests.post(
        f"{BASE_URL}/chat/message",
        json={
            "message": "Optimize my resume for Google",
            "resume_id": resume_id,
        },
        timeout=120,
    )
    data = response.json()
    print(f"Agent: {data.get('agent_type')}")
    print(f"Version: v{data.get('current_resume_version')}")

    # Export as PDF
    print("\n=== EXPORTING PDF ===")
    response = requests.post(
        f"{BASE_URL}/resume/{resume_id}/export?format=pdf",
        timeout=30,
    )
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")

    if response.status_code == 200 and "application/pdf" in response.headers.get(
        "content-type", ""
    ):
        output_path = OUTPUT_DIR / "test_optimized.pdf"
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"PDF saved to: {output_path}")
        print(f"File size: {len(response.content)} bytes")
    else:
        print(f"Export failed: {response.text[:500]}")

    # Export as DOCX
    print("\n=== EXPORTING DOCX ===")
    response = requests.post(
        f"{BASE_URL}/resume/{resume_id}/export?format=docx",
        timeout=30,
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200 and "vnd.openxmlformats" in response.headers.get(
        "content-type", ""
    ):
        output_path = OUTPUT_DIR / "test_optimized.docx"
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"DOCX saved to: {output_path}")
        print(f"File size: {len(response.content)} bytes")
    else:
        print(f"Export failed: {response.text[:500]}")

    print("\n=== EXPORT TESTS COMPLETE ===")


if __name__ == "__main__":
    test_export()
