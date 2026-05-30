import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { ChatMessage } from "../types/chat";

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

function MessageAvatar({ role }: { role: ChatMessage["role"] }) {
  return (
    <div className={`message-avatar ${role}`} aria-hidden>
      {role === "user" ? "You" : "AI"}
    </div>
  );
}

function StreamingDots() {
  return (
    <span className="streaming-dots" aria-label="Assistant is typing">
      <span />
      <span />
      <span />
    </span>
  );
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [stickToBottom, setStickToBottom] = useState(true);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    bottomRef.current?.scrollIntoView({ behavior, block: "end" });
  }, []);

  const handleScroll = useCallback(() => {
    const el = listRef.current;
    if (!el) return;

    const distanceFromBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight;
    setStickToBottom(distanceFromBottom < 96);
  }, []);

  useEffect(() => {
    if (stickToBottom) {
      scrollToBottom(isStreaming ? "instant" : "smooth");
    }
  }, [messages, isStreaming, stickToBottom, scrollToBottom]);

  return (
    <div className="message-list-wrapper">
      <div
        ref={listRef}
        className="message-list"
        onScroll={handleScroll}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
      >
        {messages.map((message) => {
          const isEmpty = !message.content.trim();
          const showThinking =
            message.status === "streaming" && isEmpty;

          return (
            <article
              key={message.id}
              className={`message ${message.role} ${message.status}`}
            >
              <MessageAvatar role={message.role} />

              <div className="message-body">
                <div className="message-meta">
                  <span className="message-author">
                    {message.role === "user" ? "You" : "Assistant"}
                  </span>
                  <time className="message-time">{message.timestamp}</time>
                </div>

                <div className="message-content">
                  {showThinking ? (
                    <div className="thinking-row">
                      <StreamingDots />
                      <span>Thinking…</span>
                    </div>
                  ) : (
                    <ReactMarkdown
                      components={{
                        code({ className, children, ...props }) {
                          const match = /language-(\w+)/.exec(
                            className ?? "",
                          );
                          const code = String(children).replace(/\n$/, "");

                          if (match) {
                            return (
                              <SyntaxHighlighter
                                style={oneDark}
                                language={match[1]}
                                PreTag="div"
                              >
                                {code}
                              </SyntaxHighlighter>
                            );
                          }

                          return (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        },
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  )}

                  {message.status === "streaming" &&
                    !showThinking &&
                    isStreaming && <StreamingDots />}
                </div>

                {message.traces?.length ? (
                  <details className="message-traces">
                    <summary>
                      Used {message.traces.length} tool
                      {message.traces.length > 1 ? "s" : ""}
                    </summary>
                    <div className="trace-items">
                      {message.traces.map((trace) => (
                        <div
                          key={`${message.id}-${trace.iteration}`}
                          className="trace-item"
                        >
                          <div className="trace-header">
                            <strong>
                              {trace.iteration}. {trace.tool_name}
                            </strong>
                            <span className="trace-meta">
                              {trace.status}
                              {trace.duration_ms != null
                                ? ` · ${trace.duration_ms}ms`
                                : ""}
                            </span>
                          </div>
                          <div className="trace-row">
                            <strong>Arguments:</strong>{" "}
                            <code>{JSON.stringify(trace.arguments)}</code>
                          </div>
                          <div className="trace-row">
                            <strong>Result:</strong>{" "}
                            <code>{trace.result_preview}</code>
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                ) : null}

                {message.status === "error" && (
                  <p className="message-error">Failed to get a response.</p>
                )}
              </div>
            </article>
          );
        })}
        <div ref={bottomRef} className="message-list-anchor" />
      </div>

      {!stickToBottom && (
        <button
          type="button"
          className="scroll-to-bottom"
          onClick={() => {
            setStickToBottom(true);
            scrollToBottom("smooth");
          }}
        >
          ↓ New messages
        </button>
      )}
    </div>
  );
}
