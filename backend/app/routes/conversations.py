from fastapi import APIRouter

from app.models.conversation_model import ConversationSummary, StoredMessage
from app.services.dynamodb_service import get_messages, list_conversations

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
async def get_conversations():
    items = await list_conversations()
    return [ConversationSummary(**item) for item in items]


@router.get("/{conversation_id}/messages", response_model=list[StoredMessage])
async def get_conversation_messages(conversation_id: str):
    items = await get_messages(conversation_id)
    return [StoredMessage(**item) for item in items]
