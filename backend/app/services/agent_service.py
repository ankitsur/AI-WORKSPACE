import json

from app.services.openai_service import (
    client,
    TOOLS
)

from app.tools.search_tool import (
    search_web
)


MAX_ITERATIONS = 5
AGENT_SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are a tool-using AI assistant.

Use the available tools when they improve factual accuracy.
If no tool is needed, continue without tool calls.
"""
}


async def run_agent(messages):

    agent_messages = [
        AGENT_SYSTEM_PROMPT,
        *messages
    ]

    iterations = 0

    while iterations < MAX_ITERATIONS:

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=agent_messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:

            return [
                item
                for item in agent_messages
                if item["role"] != "system"
            ]

        agent_messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                tc.model_dump()
                for tc in message.tool_calls
            ]
        })

        for tool_call in message.tool_calls:

            tool_name = (
                tool_call.function.name
            )

            arguments = json.loads(
                tool_call.function.arguments
            )

            tool_result = ""

            if tool_name == "search_web":

                results = await search_web(
                    arguments["query"]
                )

                tool_result = "\n\n".join([
                    f"""
Title: {result.get("title")}

Content:
{result.get("content")}
"""
                    for result in results
                ])

            agent_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        iterations += 1

    return [
        message
        for message in agent_messages
        if message["role"] != "system"
    ]