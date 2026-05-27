import { useRef, useState } from "react";

// import heroLogo from "./assets/hero.png";
import { ChatComposer } from "./components/ChatComposer";
import { MessageList } from "./components/MessageList";
import type { ChatMessage, ChatStatus } from "./types/chat";
import { streamChat } from "./utils/api";

const makeTimestamp = () =>
  new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

function App() {
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState<ChatStatus>("idle");

  // Persistent conversation ID
  const conversationId = useRef(crypto.randomUUID());

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi! How can I help you today?",
      timestamp: makeTimestamp(),
      status: "complete",
    },
  ]);

  const handleSend = async () => {
    const nextPrompt = draft.trim();

    if (!nextPrompt || status === "streaming") {
      return;
    }

    setStatus("streaming");

    const userMessage: ChatMessage = {
      id: `user-${crypto.randomUUID()}`,
      role: "user",
      content: nextPrompt,
      timestamp: makeTimestamp(),
      status: "complete",
    };

    const assistantMessageId = `assistant-${crypto.randomUUID()}`;

    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: makeTimestamp(),
      status: "streaming",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);

    setDraft("");

    try {
      await streamChat({
        conversation_id: conversationId.current,
        message: nextPrompt,

        onChunk: (chunk) => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: message.content + chunk,
                  }
                : message,
            ),
          );
        },

        onComplete: () => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    status: "complete",
                  }
                : message,
            ),
          );

          setStatus("idle");
        },

        onError: () => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: "Something went wrong.",
                    status: "error",
                  }
                : message,
            ),
          );

          setStatus("error");
        },
      });
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="chat-app">
      <div className="chat-container">
        <MessageList
          messages={messages}
          isStreaming={status === "streaming"}
        />

        <ChatComposer
          draft={draft}
          onDraftChange={setDraft}
          onSubmit={handleSend}
          isStreaming={status === "streaming"}
        />
      </div>
    </div>
  );
}

export default App;