import { useEffect, useRef, useState } from "react";
import Composer from "./components/Composer";
import MessageList from "./components/MessageList";
import Sidebar from "./components/Sidebar";
import Welcome from "./components/Welcome";
import { previewMessages } from "./data/previewMessages";
import { askRag, deleteConversation, getConversation, listConversations } from "./services/ragApi";

export default function App() {
  const preview = new URLSearchParams(location.search).get("preview") === "true";
  const [chats, setChats] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const conversation = useRef(null);
  const activeChat = chats.find(chat => chat.id === activeId);
  const messages = preview && !activeChat ? previewMessages : activeChat?.messages || [];

  useEffect(() => {
    if (preview) return;
    listConversations()
      .then(rows => setChats(rows.map(row => ({ ...row, id: row._id, messages: [] }))))
      .catch(() => setChats([]));
  }, [preview]);

  useEffect(() => {
    conversation.current?.scrollTo({
      top: conversation.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, busy]);

  const ask = async question => {
    if (busy || preview) return;
    const id = activeId;
    const temporaryId = id || `pending-${Date.now()}`;
    if (!id) {
      setActiveId(temporaryId);
      setChats(current => [{ id: temporaryId, title: question.slice(0, 80), messages: [{ role: "user", content: question }] }, ...current]);
    } else {
      setChats(current => current.map(chat => chat.id === id ? { ...chat, messages: [...chat.messages, { role: "user", content: question }] } : chat));
    }
    setBusy(true);
    try {
      const data = await askRag(question, id);
      const finalId = data.conversation_id;
      const answer = { role: "assistant", content: data.answer, sources: data.reranked_sources || [], seconds: data.timings?.total_seconds };
      setChats(current => current.map(chat => chat.id === temporaryId ? { ...chat, id: finalId, _id: finalId, messages: [...chat.messages, answer] } : chat));
      setActiveId(finalId);
    } catch (error) {
      const answer = { role: "assistant", error: true, content: `I couldn't reach the RAG pipeline. ${error.message}` };
      setChats(current => current.map(chat => chat.id === temporaryId ? { ...chat, messages: [...chat.messages, answer] } : chat));
    } finally {
      setBusy(false);
    }
  };

  const newChat = () => {
    if (!busy) {
      setActiveId(null);
      setSidebarOpen(false);
    }
  };

  const selectChat = async id => {
    if (busy) return;
    setSidebarOpen(false);
    const cached = chats.find(chat => chat.id === id);
    if (cached?.messages?.length) {
      setActiveId(id);
      return;
    }
    setBusy(true);
    try {
      const row = await getConversation(id);
      setChats(current => current.map(chat => chat.id === id ? { ...row, id: row._id } : chat));
      setActiveId(id);
    } catch (error) {
      setChats(current => current.map(chat => chat.id === id ? { ...chat, messages: [{ role: "assistant", error: true, content: `Could not load this conversation. ${error.message}` }] } : chat));
      setActiveId(id);
    } finally {
      setBusy(false);
    }
  };

  const deleteChat = async id => {
    if (busy) return;
    await deleteConversation(id);
    setChats(current => current.filter(chat => chat.id !== id));
    if (id === activeId) setActiveId(null);
  };

  return <div className="app-shell">
    <Sidebar chats={chats} activeId={activeId} open={sidebarOpen} onClose={() => setSidebarOpen(false)} onNew={newChat} onSelect={selectChat} onDelete={deleteChat}/>
    <main className="main">
      <header className="topbar">
        <button className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar">☰</button>
        <div className="model-title">CIS Controls Assistant <span>⌄</span></div>
        <button className="icon-button" onClick={newChat} aria-label="New chat">✎</button>
      </header>
      <section className="conversation" ref={conversation} aria-live="polite">
        {!messages.length && <Welcome onAsk={ask}/>}<MessageList messages={messages} busy={busy}/>
      </section>
      <Composer busy={busy || preview} onSubmit={ask}/>
    </main>
  </div>;
}
