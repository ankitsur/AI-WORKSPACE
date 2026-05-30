from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import PERSIST_FAILED_MARKER
from app.models.chat_model import ChatRequest
from app.services.agent_service import run_agent
from app.services.conversation_store import (
    append_user_message_redis,
    complete_turn,
    get_context_for_agent,
)
from app.services.openai_service import stream_ai_response

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    user_sk, user_created_at = await append_user_message_redis(
        request.conversation_id,
        user_message,
    )

    messages = await get_context_for_agent(request.conversation_id)
    messages = await run_agent(messages)

    async def generate():
        assistant_response = ""
        persist_error = False

        async for chunk in stream_ai_response(messages):
            assistant_response += chunk
            yield chunk

        try:
            await complete_turn(
                request.conversation_id,
                user_message=user_message,
                user_sk=user_sk,
                user_created_at=user_created_at,
                assistant_message=assistant_response,
            )
        except Exception:
            persist_error = True

        if persist_error:
            yield PERSIST_FAILED_MARKER

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )
