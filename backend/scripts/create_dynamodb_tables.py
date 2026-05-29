"""
Create conversations and messages tables on DynamoDB Local.

Run from backend/:
  uv run python scripts/create_dynamodb_tables.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import boto3
from botocore.exceptions import ClientError

from app.core import config

client = boto3.client(
    "dynamodb",
    endpoint_url=config.DYNAMODB_ENDPOINT_URL,
    region_name=config.AWS_REGION,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
)


def table_exists(name: str) -> bool:
    try:
        client.describe_table(TableName=name)
        return True
    except ClientError as error:
        if error.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        raise


def wait_active(name: str) -> None:
    waiter = client.get_waiter("table_exists")
    waiter.wait(TableName=name)
    while True:
        status = client.describe_table(TableName=name)["Table"]["TableStatus"]
        if status == "ACTIVE":
            return
        time.sleep(0.5)


def create_conversations_table() -> None:
    name = config.CONVERSATIONS_TABLE
    if table_exists(name):
        print(f"Table already exists: {name}")
        return

    client.create_table(
        TableName=name,
        AttributeDefinitions=[
            {"AttributeName": "conversation_id", "AttributeType": "S"},
            {"AttributeName": "list_key", "AttributeType": "S"},
            {"AttributeName": "updated_at", "AttributeType": "N"},
        ],
        KeySchema=[
            {"AttributeName": "conversation_id", "KeyType": "HASH"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_updated",
                "KeySchema": [
                    {"AttributeName": "list_key", "KeyType": "HASH"},
                    {"AttributeName": "updated_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    wait_active(name)
    print(f"Created table: {name}")


def create_messages_table() -> None:
    name = config.MESSAGES_TABLE
    if table_exists(name):
        print(f"Table already exists: {name}")
        return

    client.create_table(
        TableName=name,
        AttributeDefinitions=[
            {"AttributeName": "conversation_id", "AttributeType": "S"},
            {"AttributeName": "message_sk", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "conversation_id", "KeyType": "HASH"},
            {"AttributeName": "message_sk", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    wait_active(name)
    print(f"Created table: {name}")


def main() -> int:
    try:
        create_conversations_table()
        create_messages_table()
    except ClientError as error:
        print(f"Failed: {error}", file=sys.stderr)
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
