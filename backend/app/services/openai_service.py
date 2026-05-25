from openai import AsyncOpenAI
import os

from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


async def stream_ai_response(messages):

    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True
    )

    async for chunk in stream:

        content = chunk.choices[0].delta.content

        if content:
            yield content