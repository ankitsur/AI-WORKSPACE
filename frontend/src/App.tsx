import { useCallback, useEffect, useState } from "react";

import { ChatComposer } from "./components/ChatComposer";
import { ChatSidebar } from "./components/ChatSidebar";
import { MessageList } from "./components/MessageList";
import type {
  ChatMessage,
  ChatStatus,
  ConversationSummary,
  StoredMessage,
} from "./types/chat";
import {
  fetchConversationMessages,
  fetchConversations,
  streamChat,
} from "./utils/api";

const makeTimestamp = (iso?: string) => {
  const date = iso ? new Date(iso) : new Date();
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const welcomeMessage = (): ChatMessage => ({
  id: "welcome",
  role: "assistant",
  content: "Hi! How can I help you today?",
  timestamp: makeTimestamp(),
  status: "complete",
});

const storedToChatMessages = (stored: StoredMessage[]): ChatMessage[] =>
  stored.map((message) => ({
    id: message.message_sk,
    role: message.role,
    content: message.content,
    timestamp: makeTimestamp(message.created_at),
    status: "complete",
  }));

function App() {
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState<ChatStatus>("idle");
  const [conversations, setConversations] = useState<ConversationSummary[]>(
    [],
  );
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [persistError, setPersistError] = useState<string | null>(null);

  const [activeConversationId, setActiveConversationId] = useState(() =>
    crypto.randomUUID(),
  );
  const [messages, setMessages] = useState<ChatMessage[]>([welcomeMessage()]);

  const refreshConversations = useCallback(async () => {
    try {
      const items = await fetchConversations();
      setConversations(items);
    } catch {
      setConversations([]);
    } finally {
      setIsLoadingConversations(false);
    }
  }, []);

  useEffect(() => {
    void refreshConversations();
  }, [refreshConversations]);

  const loadConversation = async (id: string) => {
    if (status === "streaming" || id === activeConversationId) {
      return;
    }

    setIsLoadingMessages(true);
    setActiveConversationId(id);
    setPersistError(null);

    try {
      const stored = await fetchConversationMessages(id);
      setMessages(
        stored.length > 0 ? storedToChatMessages(stored) : [welcomeMessage()],
      );
    } catch {
      setMessages([welcomeMessage()]);
    } finally {
      setIsLoadingMessages(false);
      setDraft("");
      setStatus("idle");
    }
  };

  const handleNewChat = () => {
    if (status === "streaming") return;

    setActiveConversationId(crypto.randomUUID());
    setMessages([welcomeMessage()]);
    setDraft("");
    setStatus("idle");
    setPersistError(null);
  };

  const handleSend = async () => {
    const nextPrompt = draft.trim();

    if (!nextPrompt || status === "streaming") {
      return;
    }

    setStatus("streaming");
    setPersistError(null);

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

    const withoutWelcome =
      messages.length === 1 && messages[0]?.id === "welcome"
        ? []
        : messages;

    setMessages([...withoutWelcome, userMessage, assistantMessage]);
    setDraft("");

    try {
      const { persistFailed } = await streamChat({
        conversation_id: activeConversationId,
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
          void refreshConversations();
        },

        onError: () => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: "Something went wrong. Please try again.",
                    status: "error",
                  }
                : message,
            ),
          );

          setStatus("error");
        },
      });

      if (persistFailed) {
        setPersistError(
          "This conversation could not be saved. Your reply is visible here but may not appear after refresh.",
        );
      }
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="chat-app">
      <ChatSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        isLoading={isLoadingConversations}
        disabled={status === "streaming"}
        onSelect={(id) => void loadConversation(id)}
        onNewChat={handleNewChat}
      />

      <div className="chat-container">
        <header className="app-header chat-main-header">
          <div className="chat-main-title">Chat</div>
        </header>

        {status === "error" && (
          <div className="status-banner error" role="status">
            Connection issue — check that the backend is running.
          </div>
        )}

        {isLoadingMessages ? (
          <div className="messages-loading">Loading conversation…</div>
        ) : (
          <MessageList
            messages={messages}
            isStreaming={status === "streaming"}
          />
        )}

        {persistError && (
          <div className="persist-banner error" role="status">
            {persistError}
          </div>
        )}

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
