from datetime import datetime, timezone

from app.services import dynamodb_service, redis_service


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_agent_messages(messages: list[dict]) -> list[dict]:
    return [{"role": message["role"], "content": message["content"]} for message in messages]


def _is_redis_stale(redis_latest: str | None, dynamodb_latest: str | None) -> bool:
    if dynamodb_latest is None:
        return False

    if redis_latest is None:
        return True

    return redis_latest < dynamodb_latest


async def _load_from_dynamodb_and_warm(conversation_id: str) -> list[dict]:
    messages = await dynamodb_service.get_messages(conversation_id)
    await redis_service.replace_messages(conversation_id, messages)
    return messages


async def get_context_for_agent(conversation_id: str) -> list[dict]:
    redis_messages = await redis_service.get_messages(conversation_id)
    redis_latest = await redis_service.get_latest_message_sk(conversation_id)
    dynamodb_latest = await dynamodb_service.get_conversation_latest_message_sk(
        conversation_id
    )

    if not redis_messages:
        if dynamodb_latest is None:
            return []
        messages = await _load_from_dynamodb_and_warm(conversation_id)
        return _to_agent_messages(messages)

    if _is_redis_stale(redis_latest, dynamodb_latest):
        messages = await _load_from_dynamodb_and_warm(conversation_id)
        return _to_agent_messages(messages)

    return _to_agent_messages(redis_messages)


async def get_full_history(conversation_id: str) -> list[dict]:
    redis_messages = await redis_service.get_messages(conversation_id)
    redis_latest = await redis_service.get_latest_message_sk(conversation_id)
    dynamodb_latest = await dynamodb_service.get_conversation_latest_message_sk(
        conversation_id
    )

    if not redis_messages or _is_redis_stale(redis_latest, dynamodb_latest):
        return await _load_from_dynamodb_and_warm(conversation_id)

    await redis_service.replace_messages(conversation_id, redis_messages)
    return redis_messages


async def append_user_message_redis(
    conversation_id: str,
    content: str,
) -> tuple[str, str]:
    message_sk = dynamodb_service.make_message_sk()
    created_at = _iso_now()

    await redis_service.append_message(
        conversation_id,
        role="user",
        content=content,
        message_sk=message_sk,
        created_at=created_at,
    )

    return message_sk, created_at


async def complete_turn(
    conversation_id: str,
    *,
    user_message: str,
    user_sk: str,
    user_created_at: str,
    assistant_message: str,
) -> None:
    assistant_sk = dynamodb_service.make_message_sk()
    assistant_created_at = _iso_now()

    await redis_service.append_message(
        conversation_id,
        role="assistant",
        content=assistant_message,
        message_sk=assistant_sk,
        created_at=assistant_created_at,
    )

    await dynamodb_service.persist_turn(
        conversation_id,
        user_message=user_message,
        user_sk=user_sk,
        user_created_at=user_created_at,
        assistant_message=assistant_message,
        assistant_sk=assistant_sk,
        assistant_created_at=assistant_created_at,
    )
