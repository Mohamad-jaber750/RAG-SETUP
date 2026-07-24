import { apiFetch, apiJson } from "./httpClient";
import { conversationResponseSchema, conversationsResponseSchema } from "./schemas";

export async function askRag(question, conversationId) {
  return apiJson("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, conversation_id: conversationId || undefined }),
  });
}

export async function streamRag(question, conversationId, onEvent) {
  const response = await apiFetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ question, conversation_id: conversationId || undefined }),
  });
  if (!response.ok || !response.body)
    throw new Error(`Streaming request failed (${response.status})`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const line = block.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      const event = JSON.parse(line.slice(6));
      if (event.type === "error") throw new Error(event.error || "Stream failed");
      onEvent(event);
    }
    if (done) break;
  }
}

async function readEventStream(response, onEvent) {
  if (!response.ok || !response.body) throw new Error(`Request failed (${response.status})`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const line = block.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      const event = JSON.parse(line.slice(6));
      if (event.type === "error") throw new Error(event.error || "Request failed");
      onEvent(event);
    }
    if (done) break;
  }
}

export async function regenerateMessage(conversationId, messageId, onEvent) {
  const response = await apiFetch(
    `/api/conversations/${encodeURIComponent(conversationId)}/messages/${encodeURIComponent(messageId)}/regenerate`,
    { method: "POST", headers: { Accept: "text/event-stream" } },
  );
  return readEventStream(response, onEvent);
}

export async function saveMessageFeedback(conversationId, messageId, feedback) {
  return apiJson(
    `/api/conversations/${encodeURIComponent(conversationId)}/messages/${encodeURIComponent(messageId)}/feedback`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(feedback),
    },
  );
}

export async function listConversations() {
  return (await apiJson("/api/conversations", {}, conversationsResponseSchema)).conversations;
}

export async function getConversation(id) {
  return (
    await apiJson(`/api/conversations/${encodeURIComponent(id)}`, {}, conversationResponseSchema)
  ).conversation;
}

export async function deleteConversation(id) {
  return apiJson(`/api/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function checkRagHealth() {
  return apiJson("/api/health");
}
