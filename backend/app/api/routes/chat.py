"""
Chat API Routes.

Handles the main chat interface for conversational resume optimization.
"""

from uuid import uuid4

from app.agents.router import ConversationRouter
from app.models.chat import AgentAction, ChatRequest, ChatResponse
from app.models.conversation import (
    AgentType,
    Conversation,
    Message,
    MessageRole,
)
from app.services.firebase_service import (
    get_storage_service,
)
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/chat", tags=["chat"])

_router_instance: ConversationRouter | None = None
_storage_instance = None
_conversations: dict[str, Conversation] = {}
_resumes: dict[str, any] = {}


def get_router() -> ConversationRouter:
    """Get or create the conversation router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = ConversationRouter()
    return _router_instance


def get_storage():
    """Get the storage service instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = get_storage_service()
    return _storage_instance


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the chat system and receive a response.

    The system will:
    1. Route the message to the appropriate agent
    2. Process the request with the relevant resume
    3. Return the optimized resume and explanation
    """
    storage = get_storage()
    conversation_router = get_router()

    if request.conversation_id:
        conversation = await storage.get_conversation(request.conversation_id)
        if not conversation:
            conversation = await storage.create_conversation(
                user_id="default_user", resume_id=request.resume_id
            )
    else:
        conversation = await storage.create_conversation(
            user_id="default_user", resume_id=request.resume_id
        )

    if request.resume_id:
        conversation.resume_id = request.resume_id

    resume = None
    if conversation.resume_id:
        resume = await storage.get_resume(conversation.resume_id)

    user_message = Message(
        id=str(uuid4()), role=MessageRole.USER, content=request.message
    )
    conversation.add_message(user_message)

    context = {**conversation.context, **request.context}

    result = await conversation_router.route(
        user_message=request.message,
        resume=resume,
        conversation=conversation,
        context=context,
    )

    if result.updated_resume and resume:
        version = await storage.create_resume_version(
            resume_id=resume.id,
            content=result.updated_resume.get_full_text(),
            sections=result.updated_sections,
            changes_description=result.reasoning or "Resume updated",
            agent_used=result.metadata.get("agent_type", "unknown"),
        )
        conversation.current_resume_version = version.version_number

        resume.sections = result.updated_sections
        if hasattr(storage, "update_resume"):
            await storage.update_resume(resume)

    # Convert agent_type string to enum
    agent_type_str = result.metadata.get("agent_type", "router")
    agent_type_enum = AgentType(agent_type_str)

    assistant_message = Message(
        id=str(uuid4()),
        role=MessageRole.ASSISTANT,
        content=result.message,
        agent_type=agent_type_enum,
        reasoning=result.reasoning,
        actions_taken=[
            {"type": change.get("type"), "section": change.get("section")}
            for change in result.changes
        ],
    )
    conversation.add_message(assistant_message)

    if result.metadata:
        conversation.context.update(
            {
                k: v
                for k, v in result.metadata.items()
                if k in ["target_company", "target_language", "target_region"]
            }
        )

    await storage.update_conversation(conversation)

    actions = [
        AgentAction(
            agent_type=agent_type_enum,
            action=change.get("type", "modify"),
            details=change,
        )
        for change in result.changes
    ]

    resume_changes = []
    for change in result.changes:
        from app.models.chat import ResumeChange

        resume_changes.append(
            ResumeChange(
                section=change.get("section", "Unknown"),
                original_content=change.get("original_content"),
                new_content=change.get("new_content", ""),
                change_type=change.get("type", "modify"),
                reasoning=result.reasoning or "",
            )
        )

    return ChatResponse(
        message=result.message,
        conversation_id=conversation.id,
        agent_type=agent_type_enum,
        reasoning=result.reasoning,
        actions=actions,
        resume_changes=resume_changes,
        current_resume_version=conversation.current_resume_version,
        metadata=result.metadata,
    )


@router.get("/agents")
async def get_available_agents():
    """Get information about available agents."""
    conversation_router = get_router()
    return {
        "agents": conversation_router.get_available_agents(),
        "message": "Use these agents by describing what you want to do with your resume.",
    }


@router.post("/context")
async def update_context(conversation_id: str, context: dict):
    """Update the context for a conversation."""
    storage = get_storage()
    conversation = await storage.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.context.update(context)
    await storage.update_conversation(conversation)

    return {"message": "Context updated", "context": conversation.context}
