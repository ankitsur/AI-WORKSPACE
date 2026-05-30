from pydantic import BaseModel


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    updated_at: int
    last_message_preview: str | None = None


from app.models.trace_model import AgentTrace


class StoredMessage(BaseModel):
    role: str
    content: str
    created_at: str
    message_sk: str
    traces: list[AgentTrace] | None = None
