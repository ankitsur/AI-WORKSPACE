const API_BASE_URL = "http://127.0.0.1:8000";

interface StreamChatParams {
  conversation_id: string;
  message: string;
  onChunk: (chunk: string) => void;
  onComplete: () => void;
  onError: (message: string) => void;
}

export async function streamChat({
  conversation_id,
  message,
  onChunk,
  onComplete,
  onError,
}: StreamChatParams) {
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

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      const chunk = decoder.decode(value);
      onChunk(chunk);
    }

    onComplete();
  } catch (error) {
    onError(
      error instanceof Error
        ? error.message
        : "Unknown error",
    );
  }
}