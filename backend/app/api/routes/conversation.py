"""
Conversation API Routes.

Handles conversation history and management.
"""

from app.models.chat import ConversationHistoryResponse
from app.services.firebase_service import get_storage_service
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.get("/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation(conversation_id: str):
    """Get a conversation by ID with full message history."""
    storage = get_storage_service()
    conversation = await storage.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationHistoryResponse(
        conversation_id=conversation.id,
        messages=[
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "agent_type": msg.agent_type.value if msg.agent_type else None,
                "reasoning": msg.reasoning,
                "actions": msg.actions_taken,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in conversation.messages
        ],
        resume_id=conversation.resume_id,
        current_version=conversation.current_resume_version,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get("/user/{user_id}")
async def get_user_conversations(user_id: str):
    """Get all conversations for a user."""
    storage = get_storage_service()

    if hasattr(storage, "get_user_conversations"):
        conversations = await storage.get_user_conversations(user_id)
    else:
        conversations = []

    return {
        "user_id": user_id,
        "conversations": [
            {
                "id": conv.id,
                "resume_id": conv.resume_id,
                "message_count": len(conv.messages),
                "current_version": conv.current_resume_version,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "last_message": conv.messages[-1].content[:100]
                if conv.messages
                else None,
            }
            for conv in conversations
        ],
        "total": len(conversations),
    }


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    storage = get_storage_service()

    conversation = await storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if hasattr(storage, "delete_conversation"):
        await storage.delete_conversation(conversation_id)
    elif hasattr(storage, "conversations"):
        storage.conversations.pop(conversation_id, None)

    return {"message": "Conversation deleted", "conversation_id": conversation_id}


@router.get("/{conversation_id}/context")
async def get_conversation_context(conversation_id: str):
    """Get the current context for a conversation."""
    storage = get_storage_service()

    conversation = await storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation_id,
        "context": conversation.context,
        "summary": conversation.get_context_summary(),
    }


@router.post("/{conversation_id}/clear")
async def clear_conversation(conversation_id: str):
    """Clear all messages from a conversation while keeping the context."""
    storage = get_storage_service()

    conversation = await storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.messages = []
    await storage.update_conversation(conversation)

    return {
        "message": "Conversation cleared",
        "conversation_id": conversation_id,
        "context_preserved": conversation.context,
    }
