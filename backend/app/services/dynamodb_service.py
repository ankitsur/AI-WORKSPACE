from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import aioboto3
from boto3.dynamodb.conditions import Key

from app.core import config

_session = aioboto3.Session()


def _resource_kwargs() -> dict:
    return {
        "service_name": "dynamodb",
        "endpoint_url": config.DYNAMODB_ENDPOINT_URL,
        "region_name": config.AWS_REGION,
        "aws_access_key_id": config.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": config.AWS_SECRET_ACCESS_KEY,
    }


@asynccontextmanager
async def _dynamodb():
    async with _session.resource(**_resource_kwargs()) as dynamodb:
        yield dynamodb


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _preview(text: str, limit: int = 80) -> str:
    trimmed = text.strip().replace("\n", " ")
    if len(trimmed) <= limit:
        return trimmed
    return trimmed[: limit - 1] + "…"


def _title_from_message(message: str) -> str:
    trimmed = message.strip().replace("\n", " ")
    if len(trimmed) <= 60:
        return trimmed or "New chat"
    return trimmed[:59] + "…"


def _message_sk() -> str:
    return f"{_now_ms():013d}#{uuid4().hex[:8]}"


async def upsert_conversation_on_message(
    conversation_id: str,
    *,
    user_message: str | None = None,
    last_preview: str,
) -> None:
    now_ms = _now_ms()
    now_iso = _iso_now()

    async with _dynamodb() as dynamodb:
        table = await dynamodb.Table(config.CONVERSATIONS_TABLE)

        existing = await table.get_item(
            Key={"conversation_id": conversation_id},
        )
        is_new = "Item" not in existing

        title = (
            _title_from_message(user_message)
            if is_new and user_message
            else existing.get("Item", {}).get("title", "New chat")
        )

        item = {
            "conversation_id": conversation_id,
            "list_key": config.CONVERSATION_LIST_KEY,
            "updated_at": now_ms,
            "title": title,
            "last_message_preview": _preview(last_preview),
        }

        if is_new:
            item["created_at"] = now_iso

        await table.put_item(Item=item)


async def add_message(
    conversation_id: str,
    role: str,
    content: str,
) -> None:
    message_sk = _message_sk()
    created_at = _iso_now()

    async with _dynamodb() as dynamodb:
        table = await dynamodb.Table(config.MESSAGES_TABLE)
        await table.put_item(
            Item={
                "conversation_id": conversation_id,
                "message_sk": message_sk,
                "role": role,
                "content": content,
                "created_at": created_at,
            }
        )

    await upsert_conversation_on_message(
        conversation_id,
        user_message=content if role == "user" else None,
        last_preview=content,
    )


async def get_conversation_history(conversation_id: str) -> list[dict]:
    async with _dynamodb() as dynamodb:
        table = await dynamodb.Table(config.MESSAGES_TABLE)
        response = await table.query(
            KeyConditionExpression=Key("conversation_id").eq(conversation_id),
            ScanIndexForward=True,
        )

    return [
        {"role": item["role"], "content": item["content"]}
        for item in response.get("Items", [])
    ]


async def list_conversations(limit: int = 50) -> list[dict]:
    async with _dynamodb() as dynamodb:
        table = await dynamodb.Table(config.CONVERSATIONS_TABLE)
        response = await table.query(
            IndexName="by_updated",
            KeyConditionExpression=Key("list_key").eq(config.CONVERSATION_LIST_KEY),
            ScanIndexForward=False,
            Limit=limit,
        )

    return [
        {
            "conversation_id": item["conversation_id"],
            "title": item.get("title", "New chat"),
            "updated_at": int(item["updated_at"]),
            "last_message_preview": item.get("last_message_preview"),
        }
        for item in response.get("Items", [])
    ]


async def get_messages(conversation_id: str) -> list[dict]:
    async with _dynamodb() as dynamodb:
        table = await dynamodb.Table(config.MESSAGES_TABLE)
        response = await table.query(
            KeyConditionExpression=Key("conversation_id").eq(conversation_id),
            ScanIndexForward=True,
        )

    return [
        {
            "message_sk": item["message_sk"],
            "role": item["role"],
            "content": item["content"],
            "created_at": item["created_at"],
        }
        for item in response.get("Items", [])
    ]
