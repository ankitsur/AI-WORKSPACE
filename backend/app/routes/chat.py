from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.chat_model import ChatRequest

from app.services.dynamodb_service import (
    add_message,
    get_conversation_history,
)

from app.services.openai_service import (
    stream_ai_response
)

from app.services.agent_service import (
    run_agent
)

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):

    user_message = request.message

    await add_message(
        request.conversation_id,
        "user",
        user_message
    )

    messages = await get_conversation_history(
        request.conversation_id
    )

    messages = await run_agent(
        messages
    )

    async def generate():

        assistant_response = ""

        async for chunk in stream_ai_response(
            messages
        ):

            assistant_response += chunk

            yield chunk

        await add_message(
            request.conversation_id,
            "assistant",
            assistant_response
        )

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )