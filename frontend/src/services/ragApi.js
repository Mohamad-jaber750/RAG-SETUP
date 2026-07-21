async function readJson(response) {
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || data.error || "Request failed");
  return data;
}

export async function askRag(question, conversationId) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, conversation_id: conversationId || undefined })
  });
  return readJson(response);
}

export async function listConversations() {
  return (await readJson(await fetch("/api/conversations"))).conversations;
}

export async function getConversation(id) {
  return (await readJson(await fetch(`/api/conversations/${encodeURIComponent(id)}`))).conversation;
}

export async function deleteConversation(id) {
  return readJson(await fetch(`/api/conversations/${encodeURIComponent(id)}`, { method: "DELETE" }));
}

export async function checkRagHealth() {
  const response = await fetch("/api/health");
  return readJson(response);
}
