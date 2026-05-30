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


def make_message_sk() -> str:
    return f"{_now_ms():013d}#{uuid4().hex[:8]}"


async def get_conversation_latest_message_sk(conversation_id: str) -> str | None:
    async with _dynamodb() as dynamodb:
        table = await dynamodb.Table(config.CONVERSATIONS_TABLE)
        response = await table.get_item(Key={"conversation_id": conversation_id})

    item = response.get("Item")
    if not item:
        return None

    return item.get("latest_message_sk")


async def persist_turn(
    conversation_id: str,
    *,
    user_message: str,
    user_sk: str,
    user_created_at: str,
    assistant_message: str,
    assistant_sk: str,
    assistant_created_at: str,
    assistant_traces: list[dict] | None = None,
) -> None:
    now_ms = _now_ms()

    async with _dynamodb() as dynamodb:
        messages_table = await dynamodb.Table(config.MESSAGES_TABLE)
        conversations_table = await dynamodb.Table(config.CONVERSATIONS_TABLE)

        existing = await conversations_table.get_item(
            Key={"conversation_id": conversation_id},
        )
        is_new = "Item" not in existing

        title = (
            _title_from_message(user_message)
            if is_new
            else existing.get("Item", {}).get("title", "New chat")
        )

        await messages_table.put_item(
            Item={
                "conversation_id": conversation_id,
                "message_sk": user_sk,
                "role": "user",
                "content": user_message,
                "created_at": user_created_at,
            }
        )

        assistant_item = {
            "conversation_id": conversation_id,
            "message_sk": assistant_sk,
            "role": "assistant",
            "content": assistant_message,
            "created_at": assistant_created_at,
        }

        if assistant_traces is not None:
            assistant_item["traces"] = assistant_traces

        await messages_table.put_item(Item=assistant_item)

        conversation_item = {
            "conversation_id": conversation_id,
            "list_key": config.CONVERSATION_LIST_KEY,
            "updated_at": now_ms,
            "title": title,
            "last_message_preview": _preview(assistant_message),
            "latest_message_sk": assistant_sk,
        }

        if is_new:
            conversation_item["created_at"] = _iso_now()

        await conversations_table.put_item(Item=conversation_item)


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
            "traces": item.get("traces"),
        }
        for item in response.get("Items", [])
    ]
