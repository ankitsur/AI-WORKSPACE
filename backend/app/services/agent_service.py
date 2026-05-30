import json
import re
import time

from openai import BadRequestError

from app.services.openai_service import TOOLS, client, detect_tool

from app.tools.search_tool import search_web
from app.tools.python_tool import execute_python


MAX_ITERATIONS = 5
MODEL = "llama-3.3-70b-versatile"


def _preview(text: str, limit: int = 300) -> str:
    trimmed = text.strip().replace("\n", " ")
    if len(trimmed) <= limit:
        return trimmed
    return trimmed[: limit - 1] + "…"

AGENT_SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are a tool-using AI assistant.

When you need a tool, respond with a normal tool call (structured function call).
Do not write pseudo-tags like <function=...> in plain text.

Use tools only when they improve factual accuracy.
If no tool is needed, reply normally without calling tools.
""",
}

_FAILED_TOOL_RE = re.compile(
    r"<function=(\w+)(\{.*?\})</function>",
    re.DOTALL,
)


def _without_system(agent_messages: list[dict]) -> list[dict]:
    return [item for item in agent_messages if item["role"] != "system"]


def _format_search_results(results: list[dict]) -> str:
    return "\n\n".join(
        [
            f"Title: {result.get('title')}\n\nContent:\n{result.get('content')}"
            for result in results
        ]
    )


async def _execute_tool(tool_name: str, arguments: dict) -> str:
    if tool_name == "search_web":
        results = await search_web(arguments["query"])
        return _format_search_results(results)

    if tool_name == "execute_python":
        return await execute_python(arguments["code"])

    return f"Unknown tool: {tool_name}"


def _parse_failed_tool_generation(error: BadRequestError) -> tuple[str, dict] | None:
    body = getattr(error, "body", None) or {}
    failed = body.get("error", {}).get("failed_generation")
    if not failed:
        return None

    match = _FAILED_TOOL_RE.search(failed)
    if not match:
        return None

    tool_name = match.group(1)
    try:
        arguments = json.loads(match.group(2))
    except json.JSONDecodeError:
        return None

    return tool_name, arguments


async def _inject_tool_context(messages: list[dict], tool_result: str) -> list[dict]:
    return [
        *messages,
        {
            "role": "system",
            "content": (
                "Tool results (use these to answer the user's latest question):\n"
                f"{tool_result}"
            ),
        },
    ]


async def _manual_tool_fallback(
    messages: list[dict],
    error: BadRequestError | None = None,
) -> tuple[list[dict], list[dict]]:
    parsed = _parse_failed_tool_generation(error) if error else None
    traces: list[dict] = []

    if parsed:
        tool_name, arguments = parsed
        tool_result = await _execute_tool(tool_name, arguments)
        traces.append(
            {
                "iteration": 1,
                "tool_name": tool_name,
                "arguments": arguments,
                "result_preview": _preview(tool_result),
                "duration_ms": None,
                "status": "success",
                "source": "fallback",
            }
        )
        return await _inject_tool_context(messages, tool_result), traces

    last_user = next(
        (message["content"] for message in reversed(messages) if message["role"] == "user"),
        "",
    )

    if not last_user:
        return messages, traces

    routing = await detect_tool(last_user)
    if routing != "SEARCH":
        return messages, traces

    tool_result = await _execute_tool("search_web", {"query": last_user})
    traces.append(
        {
            "iteration": 1,
            "tool_name": "search_web",
            "arguments": {"query": last_user},
            "result_preview": _preview(tool_result),
            "duration_ms": None,
            "status": "success",
            "source": "fallback",
        }
    )
    return await _inject_tool_context(messages, tool_result), traces


async def run_agent(messages: list[dict]) -> tuple[list[dict], list[dict]]:
    agent_messages = [AGENT_SYSTEM_PROMPT, *messages]

    iterations = 0

    traces: list[dict] = []

    while iterations < MAX_ITERATIONS:
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                messages=agent_messages,
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
            )
        except BadRequestError as error:
            if getattr(error, "code", None) == "tool_use_failed":
                return await _manual_tool_fallback(messages, error)
            raise

        message = response.choices[0].message

        if not message.tool_calls:
            return _without_system(agent_messages), traces

        agent_messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls],
            }
        )

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            start = time.perf_counter()
            try:
                tool_result = await _execute_tool(tool_name, arguments)
                status = "success"
            except Exception as error:
                tool_result = f"Tool error: {error}"
                status = "error"
            duration_ms = int((time.perf_counter() - start) * 1000)

            traces.append(
                {
                    "iteration": len(traces) + 1,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result_preview": _preview(tool_result),
                    "duration_ms": duration_ms,
                    "status": status,
                    "source": "structured",
                }
            )

            agent_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

        iterations += 1

    return _without_system(agent_messages), traces
