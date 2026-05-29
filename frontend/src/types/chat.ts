export type ChatRole = "user" | "assistant";

export type MessageStatus =
  | "streaming"
  | "complete"
  | "error";

export type ChatStatus =
  | "idle"
  | "streaming"
  | "error";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  status: MessageStatus;
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
}
