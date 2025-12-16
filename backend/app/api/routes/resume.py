"""
Resume API Routes.

Handles resume upload, parsing, and version management.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.models.chat import (
    FileUploadResponse,
    ResumeVersionResponse,
    VersionCompareResponse,
)
from app.services.resume_parser import ResumeParserService
from app.services.firebase_service import get_storage_service
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_resume(
    file: UploadFile = File(...), user_id: str = Form(default="default_user")
):
    """
    Upload and parse a resume file.

    Supports PDF and DOCX formats. The resume will be parsed,
    sections will be extracted, and it will be indexed for search.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_extensions = ["pdf", "docx"]
    extension = file.filename.split(".")[-1].lower()
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    parser = ResumeParserService()
    storage = get_storage_service()
    vector_store = VectorStoreService()

    try:
        resume = await parser.parse_file(
            file=file.file, filename=file.filename, user_id=user_id
        )

        await storage.save_resume(resume)

        await storage.create_resume_version(
            resume_id=resume.id,
            content=resume.get_full_text(),
            sections=resume.sections,
            changes_description="Initial upload",
            agent_used="upload",
        )

        try:
            await vector_store.index_resume(resume)
        except Exception as e:
            print(f"Warning: Failed to index resume in vector store: {e}")

        sections_detected = [section.section_type.value for section in resume.sections]

        return FileUploadResponse(
            resume_id=resume.id,
            filename=resume.filename,
            message=f"Resume uploaded and parsed successfully. Found {len(resume.sections)} sections.",
            sections_detected=sections_detected,
            metadata={
                "character_count": len(resume.raw_text),
                "sections_count": len(resume.sections),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process resume: {str(e)}"
        )


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    """Get a resume by ID."""
    storage = get_storage_service()
    resume = await storage.get_resume(resume_id)

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "id": resume.id,
        "filename": resume.filename,
        "sections": [
            {
                "type": section.section_type.value,
                "title": section.title,
                "content": section.content,
            }
            for section in resume.sections
        ],
        "metadata": resume.metadata,
        "created_at": resume.created_at.isoformat(),
        "updated_at": resume.updated_at.isoformat(),
    }


@router.get("/{resume_id}/content")
async def get_resume_content(resume_id: str):
    """Get the full content of a resume."""
    storage = get_storage_service()
    resume = await storage.get_resume(resume_id)

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "id": resume.id,
        "content": resume.get_full_text(),
        "raw_text": resume.raw_text,
    }


@router.get("/{resume_id}/versions")
async def get_resume_versions(resume_id: str):
    """Get all versions of a resume."""
    storage = get_storage_service()

    resume = await storage.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    versions = await storage.get_resume_versions(resume_id)

    return {
        "resume_id": resume_id,
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "changes_description": v.changes_description,
                "agent_used": v.agent_used,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ],
        "total_versions": len(versions),
    }


@router.get("/{resume_id}/versions/{version_number}")
async def get_resume_version(resume_id: str, version_number: int):
    """Get a specific version of a resume."""
    storage = get_storage_service()

    versions = await storage.get_resume_versions(resume_id)
    version = next((v for v in versions if v.version_number == version_number), None)

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return ResumeVersionResponse(
        version_id=version.id,
        version_number=version.version_number,
        content=version.content,
        changes_description=version.changes_description,
        agent_used=version.agent_used,
        created_at=version.created_at,
    )


@router.get("/{resume_id}/compare/{version_a}/{version_b}")
async def compare_versions(resume_id: str, version_a: int, version_b: int):
    """Compare two versions of a resume."""
    storage = get_storage_service()

    versions = await storage.get_resume_versions(resume_id)
    va = next((v for v in versions if v.version_number == version_a), None)
    vb = next((v for v in versions if v.version_number == version_b), None)

    if not va or not vb:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    differences = _compute_differences(va.content, vb.content)

    return VersionCompareResponse(
        version_a=ResumeVersionResponse(
            version_id=va.id,
            version_number=va.version_number,
            content=va.content,
            changes_description=va.changes_description,
            agent_used=va.agent_used,
            created_at=va.created_at,
        ),
        version_b=ResumeVersionResponse(
            version_id=vb.id,
            version_number=vb.version_number,
            content=vb.content,
            changes_description=vb.changes_description,
            agent_used=vb.agent_used,
            created_at=vb.created_at,
        ),
        differences=differences,
    )


@router.post("/{resume_id}/revert/{version_number}")
async def revert_to_version(resume_id: str, version_number: int):
    """Revert a resume to a previous version."""
    storage = get_storage_service()

    resume = await storage.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    versions = await storage.get_resume_versions(resume_id)
    target_version = next(
        (v for v in versions if v.version_number == version_number), None
    )

    if not target_version:
        raise HTTPException(status_code=404, detail="Version not found")

    new_version = await storage.create_resume_version(
        resume_id=resume_id,
        content=target_version.content,
        sections=target_version.sections,
        changes_description=f"Reverted to version {version_number}",
        agent_used="revert",
        parent_version_id=target_version.id,
    )

    resume.sections = target_version.sections
    if hasattr(storage, "update_resume"):
        await storage.update_resume(resume)

    return {
        "message": f"Reverted to version {version_number}",
        "new_version_number": new_version.version_number,
        "version_id": new_version.id,
    }


def _compute_differences(content_a: str, content_b: str) -> list[dict]:
    """Compute differences between two content strings."""
    import difflib

    differ = difflib.unified_diff(
        content_a.splitlines(keepends=True),
        content_b.splitlines(keepends=True),
        lineterm="",
    )

    differences = []
    current_change = None

    for line in differ:
        if line.startswith("---") or line.startswith("+++"):
            continue
        elif line.startswith("@@"):
            if current_change:
                differences.append(current_change)
            current_change = {"type": "context", "lines": []}
        elif line.startswith("-"):
            if current_change is None:
                current_change = {"type": "removal", "lines": []}
            current_change["type"] = "removal"
            current_change["lines"].append(line[1:])
        elif line.startswith("+"):
            if current_change is None:
                current_change = {"type": "addition", "lines": []}
            if current_change["type"] == "removal":
                differences.append(current_change)
                current_change = {"type": "addition", "lines": []}
            current_change["type"] = "addition"
            current_change["lines"].append(line[1:])
        else:
            if current_change and current_change["lines"]:
                differences.append(current_change)
                current_change = {"type": "context", "lines": []}

    if current_change and current_change["lines"]:
        differences.append(current_change)

    return differences[:20]
