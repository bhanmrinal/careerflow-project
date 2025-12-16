"""
Entry point for running the Careerflow Resume Optimization System.
"""

import uvicorn
from backend.app.core.config import get_settings


def main():
    """Run the application."""
    settings = get_settings()

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🚀 Careerflow Resume Optimization System                    ║
    ║                                                               ║
    ║   A conversational AI system for resume optimization          ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    print(f"📍 Server: http://{settings.host}:{settings.port}")
    print(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
    print(f"🤖 LLM Provider: {settings.llm_provider.value}")
    print(f"🧠 Model: {settings.current_llm_model}")
    print()

    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_debug,
    )


if __name__ == "__main__":
    main()
