import json

import redis.asyncio as redis

from app.core import config

redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True,
)


def _messages_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}:messages"


def _meta_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}:meta"


async def _refresh_ttl(conversation_id: str) -> None:
    ttl = config.REDIS_TTL_SECONDS
    await redis_client.expire(_messages_key(conversation_id), ttl)
    await redis_client.expire(_meta_key(conversation_id), ttl)


async def append_message(
    conversation_id: str,
    *,
    role: str,
    content: str,
    message_sk: str,
    created_at: str,
) -> None:
    payload = json.dumps(
        {
            "role": role,
            "content": content,
            "message_sk": message_sk,
            "created_at": created_at,
        }
    )

    messages_key = _messages_key(conversation_id)
    meta_key = _meta_key(conversation_id)

    await redis_client.rpush(messages_key, payload)
    await redis_client.hset(meta_key, "latest_message_sk", message_sk)
    await _refresh_ttl(conversation_id)


async def replace_messages(
    conversation_id: str,
    messages: list[dict],
) -> None:
    messages_key = _messages_key(conversation_id)
    meta_key = _meta_key(conversation_id)

    await redis_client.delete(messages_key, meta_key)

    if not messages:
        return

    payloads = [json.dumps(message) for message in messages]
    await redis_client.rpush(messages_key, *payloads)
    await redis_client.hset(
        meta_key,
        "latest_message_sk",
        messages[-1]["message_sk"],
    )
    await _refresh_ttl(conversation_id)


async def get_messages(conversation_id: str) -> list[dict]:
    raw = await redis_client.lrange(_messages_key(conversation_id), 0, -1)
    return [json.loads(item) for item in raw]


async def get_latest_message_sk(conversation_id: str) -> str | None:
    return await redis_client.hget(_meta_key(conversation_id), "latest_message_sk")


async def get_conversation_history(conversation_id: str) -> list[dict]:
    messages = await get_messages(conversation_id)
    return [{"role": message["role"], "content": message["content"]} for message in messages]
