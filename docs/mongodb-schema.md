# MongoDB persistence schema

The backend stores chat history in the `rag_assistant.conversations` collection. Each
conversation embeds its messages because messages are normally loaded and deleted with
their parent conversation.

```json
{
  "_id": "uuid",
  "title": "First user question",
  "created_at": "UTC datetime",
  "updated_at": "UTC datetime",
  "messages": [
    {
      "id": "uuid",
      "role": "user | assistant",
      "content": "message text",
      "sources": [],
      "feedback": null,
      "created_at": "UTC datetime"
    }
  ]
}
```

Indexes are created for `updated_at` (conversation ordering) and `messages.id` (message
feedback and lookup extensions). The API exposes collection, detail, creation, deletion,
and chat-persistence operations under `/api/conversations` and `/api/chat`.
