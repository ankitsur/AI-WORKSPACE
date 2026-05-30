export type ChatRole = "user" | "assistant";

export type MessageStatus =
  | "streaming"
  | "complete"
  | "error";

export type ChatStatus =
  | "idle"
  | "streaming"
  | "error";

export interface AgentTrace {
  iteration: number;
  tool_name: string;
  arguments: Record<string, unknown>;
  result_preview: string;
  duration_ms?: number | null;
  status: string;
  source?: string | null;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  status: MessageStatus;
  traces?: AgentTrace[];
}

export interface ConversationSummary {
  conversation_id: string;
  title: string;
  updated_at: number;
  last_message_preview?: string | null;
}

export interface StoredMessage {
  message_sk: string;
  role: ChatRole;
  content: string;
  created_at: string;
  traces?: AgentTrace[];
}
