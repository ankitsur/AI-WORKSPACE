import { useEffect, useRef, type FormEvent } from "react";

interface ChatComposerProps {
  draft: string;
  onDraftChange: (value: string) => void;
  onSubmit: () => void;
  isStreaming: boolean;
}

export function ChatComposer({
  draft,
  onDraftChange,
  onSubmit,
  isStreaming,
}: ChatComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [draft]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  const canSend = !isStreaming && draft.trim().length > 0;

  return (
    <form className="chat-composer" onSubmit={handleSubmit}>
      <div className="composer-field">
        <textarea
          ref={textareaRef}
          className="chat-input"
          placeholder={
            isStreaming
              ? "Waiting for a response…"
              : "Ask anything… (Enter to send, Shift+Enter for newline)"
          }
          value={draft}
          onChange={(event) => onDraftChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              if (canSend) onSubmit();
            }
          }}
          disabled={isStreaming}
          rows={1}
          aria-label="Message"
        />
      </div>

      <button
        type="submit"
        className="send-button"
        disabled={!canSend}
        aria-label={isStreaming ? "Waiting for response" : "Send message"}
      >
        {isStreaming ? (
          <span className="send-spinner" aria-hidden />
        ) : (
          <svg
            className="send-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d="M22 2 11 13" />
            <path d="M22 2 15 22 11 13 2 9z" />
          </svg>
        )}
      </button>
    </form>
  );
}
