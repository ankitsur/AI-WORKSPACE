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