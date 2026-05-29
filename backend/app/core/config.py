from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "local")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "local")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

DYNAMODB_ENDPOINT_URL = os.getenv(
    "DYNAMODB_ENDPOINT_URL",
    "http://localhost:8001",
)

CONVERSATIONS_TABLE = os.getenv("CONVERSATIONS_TABLE", "conversations")
MESSAGES_TABLE = os.getenv("MESSAGES_TABLE", "messages")

CONVERSATION_LIST_KEY = "CHAT"
