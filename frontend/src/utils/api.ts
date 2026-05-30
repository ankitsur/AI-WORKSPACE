import type {
  ConversationSummary,
  StoredMessage,
} from "../types/chat";

const API_BASE_URL = "http://127.0.0.1:8000";
const PERSIST_FAILED_MARKER = "\x00__PERSIST_FAILED__";

interface StreamChatParams {
  conversation_id: string;
  message: string;
  onChunk: (chunk: string) => void;
  onComplete: () => void;
  onError: (message: string) => void;
}

interface StreamChatResult {
  persistFailed: boolean;
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  const response = await fetch(`${API_BASE_URL}/conversations`);

  if (!response.ok) {
    throw new Error("Failed to load conversations");
  }

  return response.json();
}

export async function fetchConversationMessages(
  conversationId: string,
): Promise<StoredMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}/messages`,
  );

  if (!response.ok) {
    throw new Error("Failed to load messages");
  }

  return response.json();
}

export async function streamChat({
  conversation_id,
  message,
  onChunk,
  onComplete,
  onError,
}: StreamChatParams): Promise<StreamChatResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        conversation_id,
        message,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to connect to server");
    }

    if (!response.body) {
      throw new Error("Streaming not supported");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let persistFailed = false;
    let pending = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      pending += decoder.decode(value, { stream: true });

      if (pending.includes(PERSIST_FAILED_MARKER)) {
        persistFailed = true;
        pending = pending.replace(PERSIST_FAILED_MARKER, "");
      }

      if (pending) {
        onChunk(pending);
        pending = "";
      }
    }

    pending += decoder.decode();
    if (pending.includes(PERSIST_FAILED_MARKER)) {
      persistFailed = true;
      pending = pending.replace(PERSIST_FAILED_MARKER, "");
    }
    if (pending) {
      onChunk(pending);
    }

    onComplete();
    return { persistFailed };
  } catch (error) {
    onError(
      error instanceof Error
        ? error.message
        : "Unknown error",
    );
    return { persistFailed: false };
  }
}
