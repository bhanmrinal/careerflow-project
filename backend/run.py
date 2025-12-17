"""
Entry point for running the Careerflow Resume Optimization System.
"""

import sys

import uvicorn
from app.core.config import get_settings


def main():
    """Run the application."""
    import os
    
    settings = get_settings()

    # Use UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Railway provides PORT environment variable
    port = int(os.getenv("PORT", settings.port))

    print(
        """
    ================================================================
    |                                                              |
    |   Careerflow Resume Optimization System                      |
    |                                                              |
    |   A conversational AI system for resume optimization         |
    |                                                              |
    ================================================================
    """
    )

    print(f"Server: http://{settings.host}:{port}")
    print(f"API Docs: http://{settings.host}:{port}/docs")
    print(f"LLM: Groq ({settings.groq_model})")
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=port,
        reload=settings.app_debug,
    )


if __name__ == "__main__":
    main()
