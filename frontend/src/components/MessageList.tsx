import type { ChatMessage } from "../types/chat";

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="message-list">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.role}`}
        >
          <div className="message-content">
            {message.content || "Thinking..."}
          </div>
        </div>
      ))}
    </div>
  );
}