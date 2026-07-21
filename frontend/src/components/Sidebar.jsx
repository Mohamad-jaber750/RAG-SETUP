export default function Sidebar({ chats, activeId, open, onClose, onNew, onSelect, onDelete }) {
  return <>
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="brand-row">
        <div className="brand-mark" aria-hidden="true">C</div>
        <div><strong>CIS Assistant</strong><span>Controls v8</span></div>
        <button className="icon-button mobile-close" onClick={onClose} aria-label="Close sidebar">×</button>
      </div>
      <button className="new-chat" onClick={onNew}><span>＋</span> New chat</button>
      <div className="history-label">Recent</div>
      <nav className="history" aria-label="Chat history">
        {!chats.length && <div className="empty-history">No conversations yet</div>}
        {chats.map(chat => <div className={`history-item ${chat.id === activeId ? "active" : ""}`} key={chat.id}>
          <button className="history-select" title={chat.title} onClick={() => onSelect(chat.id)}>{chat.title}</button>
          <button className="history-delete" aria-label={`Delete ${chat.title}`} onClick={() => onDelete(chat.id)}>×</button>
        </div>)}
      </nav>
      <div className="sidebar-footer"><div className="status-dot"/><div><strong>Local & private</strong><span>Your data stays on this machine</span></div></div>
    </aside>
    <button className={`scrim ${open ? "open" : ""}`} onClick={onClose} aria-label="Close navigation" />
  </>;
}
