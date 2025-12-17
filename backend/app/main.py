"""
Careerflow Resume Optimization System - Main Application.

A conversational AI system for resume optimization using specialized agents.
"""

import os
from contextlib import asynccontextmanager

from app.api.routes import chat_router, conversation_router, resume_router
from app.core.config import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    os.makedirs(settings.upload_directory, exist_ok=True)
    os.makedirs(settings.chroma_persist_directory, exist_ok=True)

    print(f"[START] {settings.app_name} starting...")
    print(f"[DIR] Upload directory: {settings.upload_directory}")
    print(f"[DB] ChromaDB directory: {settings.chroma_persist_directory}")
    print(f"[LLM] Groq ({settings.groq_model})")

    yield

    print("[STOP] Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="""
        A conversational AI system for resume optimization.

        ## Features

        - **Company Research & Optimization**: Research companies and tailor resumes
        - **Job Description Matching**: Analyze JDs and calculate match scores
        - **Translation & Localization**: Translate resumes for different markets

        ## How to Use

        1. Upload your resume (PDF or DOCX)
        2. Start a conversation describing what you want to optimize
        3. The system will route your request to the appropriate agent
        4. Review the optimized resume and agent reasoning
        """,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router, prefix="/api")
    app.include_router(resume_router, prefix="/api")
    app.include_router(conversation_router, prefix="/api")

    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")

        @app.get("/")
        async def serve_frontend():
            """Serve the frontend application."""
            index_path = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"message": "Frontend not found. API is running at /docs"}

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": "1.0.0",
            "llm": f"Groq ({settings.groq_model})",
        }

    @app.get("/api/info")
    async def get_info():
        """Get application information."""
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "description": "Conversational Resume Optimization System",
            "features": [
                "Company Research & Optimization",
                "Job Description Matching",
                "Translation & Localization",
            ],
            "supported_file_types": settings.allowed_extensions,
            "llm": f"Groq ({settings.groq_model})",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_debug,
    )
