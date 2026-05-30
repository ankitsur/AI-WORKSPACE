import type {
  AgentTrace,
  ConversationSummary,
  StoredMessage,
} from "../types/chat";

const API_BASE_URL = "http://127.0.0.1:8000";
const PERSIST_FAILED_MARKER = "\x00__PERSIST_FAILED__";
const TRACE_START = "\x00__TRACES__BEGIN__";
const TRACE_END = "\x00__TRACES__END__";

interface StreamChatParams {
  conversation_id: string;
  message: string;
  onChunk: (chunk: string) => void;
  onTraces: (traces: AgentTrace[]) => void;
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
  onTraces,
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

    const drainPending = () => {
      while (true) {
        const traceStart = pending.indexOf(TRACE_START);
        const persistIdx = pending.indexOf(PERSIST_FAILED_MARKER);

        if (persistIdx >= 0 && (traceStart === -1 || persistIdx < traceStart)) {
          pending = pending.replace(PERSIST_FAILED_MARKER, "");
          persistFailed = true;
          continue;
        }

        if (traceStart >= 0) {
          const contentBeforeTrace = pending.slice(0, traceStart);
          if (contentBeforeTrace) {
            onChunk(contentBeforeTrace);
          }

          const traceEnd = pending.indexOf(TRACE_END, traceStart + TRACE_START.length);
          if (traceEnd === -1) {
            pending = pending.slice(traceStart);
            break;
          }

          const traceJson = pending.slice(
            traceStart + TRACE_START.length,
            traceEnd,
          );

          try {
            onTraces(JSON.parse(traceJson));
          } catch {
            // Ignore malformed trace metadata.
          }

          pending = pending.slice(traceEnd + TRACE_END.length);
          continue;
        }

        break;
      }

      if (pending && !pending.startsWith(TRACE_START)) {
        onChunk(pending);
        pending = "";
      }
    };

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      pending += decoder.decode(value, { stream: true });
      drainPending();
    }

    pending += decoder.decode();
    drainPending();

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
