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

export async function streamRag(question, conversationId, onEvent) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
    body: JSON.stringify({ question, conversation_id: conversationId || undefined })
  });
  if (!response.ok || !response.body) throw new Error(`Streaming request failed (${response.status})`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const line = block.split("\n").find(item => item.startsWith("data: "));
      if (!line) continue;
      const event = JSON.parse(line.slice(6));
      if (event.type === "error") throw new Error(event.error || "Stream failed");
      onEvent(event);
    }
    if (done) break;
  }
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
