import { useEffect, useRef, useState } from "react";
import Composer from "@/components/Composer";
import MessageList from "@/components/MessageList";
import Sidebar from "@/components/Sidebar";
import Welcome from "@/components/Welcome";
import GuidedTour from "@/components/GuidedTour";
import useAuth from "@/hooks/useAuth";
import useChatWorkspace from "@/hooks/useChatWorkspace";

export default function App() {
  const { user, preview, signOut } = useAuth();
  const workspace = useChatWorkspace({ enabled: Boolean(user), preview });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const conversation = useRef(null);

  useEffect(() => {
    conversation.current?.scrollTo({
      top: conversation.current.scrollHeight,
      behavior: "smooth",
    });
  }, [workspace.messages, workspace.busy]);

  const newChat = () => {
    workspace.newChat();
    setSidebarOpen(false);
  };

  const selectChat = async (id) => {
    setSidebarOpen(false);
    await workspace.selectChat(id);
  };

  const handleSignOut = async () => {
    await signOut();
    workspace.reset();
  };

  return (
    <div className="app-shell">
      <Sidebar
        chats={workspace.chats}
        activeId={workspace.activeId}
        open={sidebarOpen}
        user={user}
        onClose={() => setSidebarOpen(false)}
        onNew={newChat}
        onSelect={selectChat}
        onDelete={workspace.deleteChat}
        onLogout={handleSignOut}
      />
      <main className="main">
        <header className="topbar">
          <button
            className="icon-button menu-button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            ☰
          </button>
          <h1 className="model-title">
            CIS Controls Assistant <span>⌄</span>
          </h1>
          <button className="icon-button" onClick={newChat} aria-label="New chat">
            ✎
          </button>
        </header>
        <section className="conversation" ref={conversation} aria-live="polite">
          {workspace.error && (
            <div className="page-error error-box" role="alert">
              {workspace.error}
            </div>
          )}
          {!workspace.messages.length && <Welcome onAsk={workspace.ask} />}
          <MessageList
            messages={workspace.messages}
            busy={workspace.busy}
            onRegenerate={workspace.regenerate}
            onSelectVersion={workspace.selectVersion}
            onFeedback={workspace.submitFeedback}
          />
        </section>
        <Composer busy={workspace.busy || preview} onSubmit={workspace.ask} />
      </main>
      <GuidedTour />
    </div>
  );
}
