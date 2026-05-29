import type { ConversationSummary } from "../types/chat";

interface ChatSidebarProps {
  conversations: ConversationSummary[];
  activeConversationId: string;
  isLoading: boolean;
  disabled: boolean;
  onSelect: (conversationId: string) => void;
  onNewChat: () => void;
}

function formatRelativeTime(epochMs: number): string {
  const diff = Date.now() - epochMs;
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(epochMs).toLocaleDateString();
}

export function ChatSidebar({
  conversations,
  activeConversationId,
  isLoading,
  disabled,
  onSelect,
  onNewChat,
}: ChatSidebarProps) {
  return (
    <aside className="chat-sidebar" aria-label="Chat history">
      <div className="sidebar-header">
        <div className="brand-mark">
          <div className="brand-logo" aria-hidden>
            AI
          </div>
          <div>
            <div className="brand-label">AI Workspace</div>
            <div className="brand-subtitle">Your chats</div>
          </div>
        </div>
        <button
          type="button"
          className="new-chat-button sidebar-new-chat"
          onClick={onNewChat}
          disabled={disabled}
        >
          New chat
        </button>
      </div>

      <div className="sidebar-list" role="list">
        {isLoading && (
          <p className="sidebar-empty">Loading chats…</p>
        )}

        {!isLoading && conversations.length === 0 && (
          <p className="sidebar-empty">No chats yet. Start a conversation.</p>
        )}

        {!isLoading &&
          conversations.map((conversation) => {
            const isActive =
              conversation.conversation_id === activeConversationId;

            return (
              <button
                key={conversation.conversation_id}
                type="button"
                role="listitem"
                className={`sidebar-item${isActive ? " active" : ""}`}
                onClick={() => onSelect(conversation.conversation_id)}
                disabled={disabled}
              >
                <span className="sidebar-item-title">{conversation.title}</span>
                {conversation.last_message_preview && (
                  <span className="sidebar-item-preview">
                    {conversation.last_message_preview}
                  </span>
                )}
                <span className="sidebar-item-time">
                  {formatRelativeTime(conversation.updated_at)}
                </span>
              </button>
            );
          })}
      </div>
    </aside>
  );
}
