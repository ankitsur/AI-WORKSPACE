import type { FormEvent } from "react";

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
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form className="chat-composer" onSubmit={handleSubmit}>
      <textarea
        className="chat-input"
        placeholder="Ask anything..."
        value={draft}
        onChange={(event) => onDraftChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSubmit();
          }
        }}
        disabled={isStreaming}
        rows={3}
      />

      <button
        type="submit"
        className="send-button"
        disabled={isStreaming || !draft.trim()}
      >
        {isStreaming ? "Thinking..." : "Send"}
      </button>
    </form>
  );
}