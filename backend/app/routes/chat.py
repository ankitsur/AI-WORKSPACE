from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.chat_model import ChatRequest

from app.services.redis_service import (
    add_message,
    get_conversation_history
)

from app.tools.search_tool import (
    search_web
)

from app.services.openai_service import (
    stream_ai_response,
    detect_tool
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

    tool_decision = await detect_tool(
        user_message
    )

    print(
        f"Tool Decision: {tool_decision}"
    )

    if tool_decision == "SEARCH":

        results = await search_web(
            user_message
        )

        print(
            f"Search Results Count: {len(results)}"
        )

        search_context = "\n\n".join([
            f"""
Title: {result.get("title")}

Content:
{result.get("content")}
"""
            for result in results
        ])

        messages.append({
            "role": "system",
            "content": f"""
You are provided with
web search results below.

Use them to answer accurately.

Web Search Results:

{search_context}
"""
        })

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