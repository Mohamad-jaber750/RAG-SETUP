from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection


load_dotenv()


class MongoRepository:
    """Persists conversations as documents with embedded messages."""

    def __init__(self) -> None:
        self._client: MongoClient | None = None
        self._conversations: Collection | None = None

    @property
    def conversations(self) -> Collection:
        if self._conversations is None:
            uri = os.getenv("MONGODB_URI")
            if not uri:
                raise RuntimeError("MONGODB_URI is not configured.")
            database_name = os.getenv("MONGODB_DATABASE", "rag_assistant")
            self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self._client.admin.command("ping")
            self._conversations = self._client[database_name]["conversations"]
            self._conversations.create_index([("updated_at", DESCENDING)])
            self._conversations.create_index([("messages.id", ASCENDING)])
        return self._conversations

    def ping(self) -> bool:
        _ = self.conversations
        return True

    def create_conversation(self, title: str) -> dict[str, Any]:
        now = datetime.now(UTC)
        conversation = {
            "_id": str(uuid4()),
            "title": title.strip()[:80] or "New conversation",
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        self.conversations.insert_one(conversation)
        return self._serialize(conversation)

    def list_conversations(self, limit: int = 50) -> list[dict[str, Any]]:
        projection = {"messages": 0}
        rows = self.conversations.find({}, projection).sort("updated_at", DESCENDING).limit(limit)
        return [self._serialize(row) for row in rows]

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        row = self.conversations.find_one({"_id": conversation_id})
        return self._serialize(row) if row else None

    def delete_conversation(self, conversation_id: str) -> bool:
        return self.conversations.delete_one({"_id": conversation_id}).deleted_count == 1

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        message = {
            "id": str(uuid4()),
            "role": role,
            "content": content,
            "sources": sources or [],
            "feedback": None,
            "versions": [],
            "active_version": 0,
            "created_at": now,
        }
        result = self.conversations.update_one(
            {"_id": conversation_id},
            {"$push": {"messages": message}, "$set": {"updated_at": now}},
        )
        if result.matched_count == 0:
            raise KeyError("Conversation not found.")
        return self._serialize(message)

    def get_message(self, conversation_id: str, message_id: str) -> dict[str, Any] | None:
        row = self.conversations.find_one(
            {"_id": conversation_id, "messages.id": message_id},
            {"messages.$": 1},
        )
        return self._serialize(row["messages"][0]) if row and row.get("messages") else None

    def add_message_version(
        self,
        conversation_id: str,
        message_id: str,
        content: str,
        sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        message = self.get_message(conversation_id, message_id)
        if message is None:
            raise KeyError("Message not found.")
        versions = message.get("versions") or [
            {
                "content": message["content"],
                "sources": message.get("sources", []),
                "created_at": message.get("created_at"),
            }
        ]
        versions.append(
            {
                "content": content,
                "sources": sources,
                "created_at": datetime.now(UTC),
            }
        )
        active_version = len(versions) - 1
        result = self.conversations.update_one(
            {"_id": conversation_id, "messages.id": message_id},
            {
                "$set": {
                    "messages.$.content": content,
                    "messages.$.sources": sources,
                    "messages.$.versions": versions,
                    "messages.$.active_version": active_version,
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        if result.matched_count == 0:
            raise KeyError("Message not found.")
        return self.get_message(conversation_id, message_id) or {}

    def set_feedback(
        self,
        conversation_id: str,
        message_id: str,
        rating: str,
        reasons: list[str],
        comment: str,
    ) -> dict[str, Any]:
        feedback = {
            "rating": rating,
            "reasons": reasons,
            "comment": comment,
            "created_at": datetime.now(UTC),
        }
        result = self.conversations.update_one(
            {"_id": conversation_id, "messages.id": message_id},
            {
                "$set": {
                    "messages.$.feedback": feedback,
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        if result.matched_count == 0:
            raise KeyError("Message not found.")
        return self._serialize(feedback)

    @classmethod
    def _serialize(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [cls._serialize(item) for item in value]
        if isinstance(value, dict):
            return {key: cls._serialize(item) for key, item in value.items()}
        return value

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

