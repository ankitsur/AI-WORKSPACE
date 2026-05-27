import type { ChatMessage } from "../types/chat";
import ReactMarkdown from "react-markdown";


interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}


export function MessageList({
  messages,
  isStreaming,
}: MessageListProps) {
  return (
    <div className="message-list">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.role}`}
        >
          <div className="message-content">
            <ReactMarkdown>
              {message.content || (isStreaming ? "Thinking..." : "")}
            </ReactMarkdown>
          </div>
        </div>
      ))}
    </div>
  );
}