import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { previewMessages } from "@/data/previewMessages";
import {
  deleteConversation,
  getConversation,
  listConversations,
  regenerateMessage,
  saveMessageFeedback,
  streamRag,
} from "@/services/ragApi";

const conversationKeys = {
  all: ["conversations"],
  detail: (id) => ["conversations", id],
};

export default function useChatWorkspace({ enabled, preview }) {
  const queryClient = useQueryClient();
  const [localChats, setLocalChats] = useState(null);
  const [activeId, setActiveId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [operationError, setOperationError] = useState("");

  const conversationsQuery = useQuery({
    queryKey: conversationKeys.all,
    queryFn: listConversations,
    enabled: enabled && !preview,
  });

  const serverChats = useMemo(
    () =>
      (conversationsQuery.data || []).map((row) => ({
        ...row,
        id: row._id,
        messages: row.messages || [],
      })),
    [conversationsQuery.data],
  );
  const chats = localChats ?? serverChats;
  const updateChats = (updater) => setLocalChats((current) => updater(current ?? serverChats));

  const deleteMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: (_, id) => {
      updateChats((current) => current.filter((chat) => chat.id !== id));
      setActiveId((current) => (current === id ? null : current));
      queryClient.invalidateQueries({ queryKey: conversationKeys.all });
    },
    onError: (error) => setOperationError(`Could not delete the conversation. ${error.message}`),
  });

  const activeChat = chats.find((chat) => chat.id === activeId);
  const messages = useMemo(
    () => (preview && !activeChat ? previewMessages : activeChat?.messages || []),
    [activeChat, preview],
  );
  const error =
    operationError ||
    (conversationsQuery.error
      ? `Could not load conversations. ${conversationsQuery.error.message}`
      : "");

  const ask = async (question) => {
    if (busy || preview) return;
    setOperationError("");

    const id = activeId?.startsWith("pending-") ? null : activeId;
    const temporaryId = id || `pending-${crypto.randomUUID()}`;
    const userMessage = { id: crypto.randomUUID(), role: "user", content: question };

    if (!id) {
      setActiveId(temporaryId);
      updateChats((current) => [
        {
          id: temporaryId,
          title: question.slice(0, 80),
          messages: [userMessage],
        },
        ...current,
      ]);
    } else {
      updateChats((current) =>
        current.map((chat) =>
          chat.id === id ? { ...chat, messages: [...chat.messages, userMessage] } : chat,
        ),
      );
    }

    setBusy(true);
    let currentId = temporaryId;

    try {
      const updateAssistant = (patch) =>
        updateChats((current) =>
          current.map((chat) => {
            if (chat.id !== currentId) return chat;
            const nextMessages = [...chat.messages];
            const last = nextMessages.at(-1);
            if (last?.role === "assistant" && last.streaming) {
              nextMessages[nextMessages.length - 1] = { ...last, ...patch };
            } else {
              nextMessages.push({
                id: crypto.randomUUID(),
                role: "assistant",
                content: "",
                sources: [],
                streaming: true,
                ...patch,
              });
            }
            return { ...chat, messages: nextMessages };
          }),
        );

      await streamRag(question, id, (event) => {
        if (event.type === "start") {
          const finalId = event.conversation_id;
          const previousId = currentId;
          updateChats((current) =>
            current.map((chat) =>
              chat.id === previousId ? { ...chat, id: finalId, _id: finalId } : chat,
            ),
          );
          currentId = finalId;
          setActiveId(finalId);
        } else if (event.type === "sources") {
          updateAssistant({ sources: event.sources });
        } else if (event.type === "token") {
          updateChats((current) =>
            current.map((chat) =>
              chat.id === currentId
                ? {
                    ...chat,
                    messages: chat.messages.map((message, index) =>
                      index === chat.messages.length - 1 && message.role === "assistant"
                        ? { ...message, content: message.content + event.token, streaming: true }
                        : message,
                    ),
                  }
                : chat,
            ),
          );
        } else if (event.type === "timings") {
          updateAssistant({ seconds: event.timings.total_seconds });
        } else if (event.type === "done") {
          updateAssistant({ streaming: false, id: event.message_id });
          queryClient.invalidateQueries({ queryKey: conversationKeys.all });
        }
      });
    } catch (streamError) {
      const answer = {
        id: crypto.randomUUID(),
        role: "assistant",
        error: true,
        content: `I couldn't reach the RAG pipeline. ${streamError.message}`,
      };
      updateChats((current) =>
        current.map((chat) =>
          chat.id === currentId ? { ...chat, messages: [...chat.messages, answer] } : chat,
        ),
      );
    } finally {
      setBusy(false);
    }
  };

  const selectChat = async (id) => {
    if (busy) return;
    setOperationError("");

    const cached = chats.find((chat) => chat.id === id);
    if (cached?.messages?.length) {
      setActiveId(id);
      return;
    }

    setBusy(true);
    try {
      const row = await queryClient.fetchQuery({
        queryKey: conversationKeys.detail(id),
        queryFn: () => getConversation(id),
      });
      updateChats((current) =>
        current.map((chat) => (chat.id === id ? { ...row, id: row._id } : chat)),
      );
      setActiveId(id);
    } catch (loadError) {
      setOperationError(`Could not load this conversation. ${loadError.message}`);
    } finally {
      setBusy(false);
    }
  };

  const newChat = () => {
    if (!busy) setActiveId(null);
  };

  const patchMessage = (messageId, patch) =>
    updateChats((current) =>
      current.map((chat) =>
        chat.id === activeId
          ? {
              ...chat,
              messages: chat.messages.map((message) =>
                message.id === messageId ? { ...message, ...patch } : message,
              ),
            }
          : chat,
      ),
    );

  const regenerate = async (message) => {
    if (busy || !activeId || !message.id) return;
    setBusy(true);
    setOperationError("");
    const original = { content: message.content, sources: message.sources || [] };
    patchMessage(message.id, { content: "", sources: [], streaming: true });
    try {
      await regenerateMessage(activeId, message.id, (event) => {
        if (event.type === "token") {
          updateChats((current) =>
            current.map((chat) =>
              chat.id === activeId
                ? {
                    ...chat,
                    messages: chat.messages.map((item) =>
                      item.id === message.id
                        ? { ...item, content: item.content + event.token, streaming: true }
                        : item,
                    ),
                  }
                : chat,
            ),
          );
        } else if (event.type === "sources") {
          patchMessage(message.id, { sources: event.sources });
        } else if (event.type === "done") {
          patchMessage(message.id, { ...event.message, streaming: false });
        }
      });
    } catch (regenerateError) {
      patchMessage(message.id, { ...original, streaming: false });
      setOperationError(`Could not regenerate the answer. ${regenerateError.message}`);
    } finally {
      setBusy(false);
    }
  };

  const selectVersion = (message, index) => {
    const version = message.versions?.[index];
    if (version) {
      patchMessage(message.id, {
        content: version.content,
        sources: version.sources || [],
        active_version: index,
      });
    }
  };

  const submitFeedback = async (messageId, feedback) => {
    if (!activeId) return;
    const response = await saveMessageFeedback(activeId, messageId, feedback);
    patchMessage(messageId, { feedback: response.feedback });
  };

  const reset = () => {
    setLocalChats(null);
    setActiveId(null);
    queryClient.removeQueries({ queryKey: conversationKeys.all });
  };

  return {
    chats,
    activeId,
    messages,
    busy,
    error,
    ask,
    newChat,
    selectChat,
    deleteChat: (id) => !busy && deleteMutation.mutate(id),
    regenerate,
    selectVersion,
    submitFeedback,
    reset,
  };
}
