from pydantic import BaseModel


class AgentTrace(BaseModel):
    iteration: int
    tool_name: str
    arguments: dict
    result_preview: str