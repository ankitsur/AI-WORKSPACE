import redis.asyncio as redis
import json

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

async def add_message(
    conversation_id: str,
    role: str,
    content: str
):

    key = f"conversation:{conversation_id}"

    message = {
        "role": role,
        "content": content
    }

    await redis_client.rpush(
        key,
        json.dumps(message)
    )

async def get_conversation_history(
    conversation_id: str
):

    key = f"conversation:{conversation_id}"

    messages = await redis_client.lrange(
        key,
        0,
        -1
    )

    return [
        json.loads(message)
        for message in messages
    ]