import PropTypes from "prop-types";
import { chatPropType, userPropType } from "@/shared/propTypes";

export default function Sidebar({
  chats,
  activeId,
  open,
  user,
  onClose,
  onNew,
  onSelect,
  onDelete,
  onLogout,
}) {
  return (
    <>
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark" aria-hidden="true">
            C
          </div>
          <div>
            <strong>CIS Assistant</strong>
            <span>Controls v8</span>
          </div>
          <button className="icon-button mobile-close" onClick={onClose} aria-label="Close sidebar">
            ×
          </button>
        </div>
        <button className="new-chat" onClick={onNew}>
          <span aria-hidden="true">＋</span> New chat
        </button>
        <div className="history-label">Recent</div>
        <nav className="history" aria-label="Chat history">
          {!chats.length && <div className="empty-history">No conversations yet</div>}
          {chats.map((chat) => (
            <div className={`history-item ${chat.id === activeId ? "active" : ""}`} key={chat.id}>
              <button
                className="history-select"
                title={chat.title}
                onClick={() => onSelect(chat.id)}
              >
                {chat.title}
              </button>
              <button
                className="history-delete"
                aria-label={`Delete ${chat.title}`}
                onClick={() => onDelete(chat.id)}
              >
                ×
              </button>
            </div>
          ))}
        </nav>
        <div className="sidebar-footer user-footer">
          {user.avatarUrl ? (
            <img className="user-avatar" src={user.avatarUrl} alt="" />
          ) : (
            <div className="user-avatar user-initial" aria-hidden="true">
              {(user.displayName || user.email || "U").charAt(0).toUpperCase()}
            </div>
          )}
          <div className="user-details">
            <strong>{user.displayName || "Signed in"}</strong>
            <span>{user.email}</span>
          </div>
          <button
            className="logout-button"
            onClick={onLogout}
            title="Sign out"
            aria-label="Sign out"
          >
            ↪
          </button>
        </div>
      </aside>
      <button
        className={`scrim ${open ? "open" : ""}`}
        onClick={onClose}
        aria-label="Close navigation"
      />
    </>
  );
}

Sidebar.propTypes = {
  chats: PropTypes.arrayOf(chatPropType).isRequired,
  activeId: PropTypes.string,
  open: PropTypes.bool.isRequired,
  user: userPropType.isRequired,
  onClose: PropTypes.func.isRequired,
  onNew: PropTypes.func.isRequired,
  onSelect: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onLogout: PropTypes.func.isRequired,
};
