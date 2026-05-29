from openai import AsyncOpenAI
import os

from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1"
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for recent or factual information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": """
Execute Python code for calculations,
data processing and analysis.
""",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string", "description": "The Python code to execute."}},
                "required": ["code"],
            },
        },
    },
]


async def detect_tool(user_message: str):

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
You are a tool routing assistant.

Your task:
Determine whether the user needs
web search.

Return ONLY:

SEARCH

or

NONE
""",
            },
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()


async def stream_ai_response(messages):

    system_prompt = {
        "role": "system",
        "content": """
You are an AI research assistant.

Answer clearly and accurately.

If web search context is provided,
use it to answer the user question.
""",
    }

    final_messages = [system_prompt, *messages]

    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile", messages=final_messages, stream=True
    )

    async for chunk in stream:

        content = chunk.choices[0].delta.content

        if content:
            yield content
