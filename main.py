from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
REACT_BUILD_DIR = ROOT / "frontend" / "dist"
STATIC_DIR = REACT_BUILD_DIR if REACT_BUILD_DIR.exists() else ROOT / "static"
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from database import MongoRepository


class RAGService:
    """Lazily creates one pipeline and serializes model requests."""

    def __init__(self) -> None:
        self._pipeline: Any | None = None
        self._lock = threading.Lock()

    def answer(self, question: str) -> dict[str, Any]:
        with self._lock:
            if self._pipeline is None:
                from pipeline import RAGPipeline

                self._pipeline = RAGPipeline()
            return self._pipeline.answer(question)

    def initialize(self) -> None:
        """Initialize connections and warm models before accepting requests."""
        with self._lock:
            if self._pipeline is None:
                from pipeline import RAGPipeline
                try:
                    self._pipeline = RAGPipeline()
                except Exception:
                    if self._pipeline is not None:
                        self._pipeline.close()
                        self._pipeline = None
                    raise

    def stream_answer(self, question: str):
        with self._lock:
            if self._pipeline is None:
                from pipeline import RAGPipeline

                self._pipeline = RAGPipeline()
            yield from self._pipeline.stream_answer(question)

    def close(self) -> None:
        if self._pipeline is not None:
            self._pipeline.close()


SERVICE = RAGService()
DATABASE = MongoRepository()


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            ui_url = os.getenv("PUBLIC_UI_URL", "http://localhost:5127")
            self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
            self.send_header("Location", ui_url)
            self.end_headers()
            return
        if path == "/api/health":
            try:
                DATABASE.ping()
                database_status = "connected"
            except Exception:
                database_status = "unavailable"
            self._send_json({"status": "ok", "database": database_status})
            return
        if path == "/api/conversations":
            self._send_json({"conversations": DATABASE.list_conversations()})
            return
        if path.startswith("/api/conversations/"):
            conversation_id = path.rsplit("/", 1)[-1]
            conversation = DATABASE.get_conversation(conversation_id)
            if conversation is None:
                self._send_json({"error": "Conversation not found."}, HTTPStatus.NOT_FOUND)
            else:
                self._send_json({"conversation": conversation})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")
        if len(parts) == 6 and parts[:2] == ["api", "conversations"] and parts[3] == "messages" and parts[5] == "regenerate":
            self._regenerate(parts[2], parts[4])
            return
        if len(parts) == 6 and parts[:2] == ["api", "conversations"] and parts[3] == "messages" and parts[5] == "feedback":
            self._save_feedback(parts[2], parts[4])
            return
        if path == "/api/conversations":
            self._create_conversation()
            return
        if path == "/api/chat/stream":
            self._stream_chat()
            return
        if path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            question = str(payload.get("question", "")).strip()
            if not question:
                self._send_json({"error": "Please enter a question."}, HTTPStatus.BAD_REQUEST)
                return
            if len(question) > 4000:
                self._send_json({"error": "Question is too long (maximum 4,000 characters)."}, HTTPStatus.BAD_REQUEST)
                return

            conversation_id = str(payload.get("conversation_id", "")).strip()
            if not conversation_id or DATABASE.get_conversation(conversation_id) is None:
                conversation = DATABASE.create_conversation(question)
                conversation_id = conversation["_id"]
            DATABASE.add_message(conversation_id, "user", question)
            result = SERVICE.answer(question)
            assistant_message = DATABASE.add_message(
                conversation_id,
                "assistant",
                result["answer"],
                result.get("reranked_sources", []),
            )
            result["conversation_id"] = conversation_id
            result["message_id"] = assistant_message["id"]
            self._send_json(result)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid request body."}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            print(f"Chat request failed: {exc}", file=sys.stderr)
            self._send_json(
                {"error": "The RAG service could not answer right now.", "detail": str(exc)},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _stream_chat(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            question = str(payload.get("question", "")).strip()
            if not question:
                self._send_json({"error": "Please enter a question."}, HTTPStatus.BAD_REQUEST)
                return

            conversation_id = str(payload.get("conversation_id", "")).strip()
            if not conversation_id or DATABASE.get_conversation(conversation_id) is None:
                conversation_id = DATABASE.create_conversation(question)["_id"]
            DATABASE.add_message(conversation_id, "user", question)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            self._send_sse({"type": "start", "conversation_id": conversation_id})

            answer_parts: list[str] = []
            sources: list[dict[str, Any]] = []
            timings: dict[str, float] = {}
            for event in SERVICE.stream_answer(question):
                if event["type"] == "token":
                    answer_parts.append(event["token"])
                elif event["type"] == "sources":
                    sources = event["sources"]
                elif event["type"] == "timings":
                    timings = event["timings"]
                self._send_sse(event)

            message = DATABASE.add_message(conversation_id, "assistant", "".join(answer_parts).strip(), sources)
            self._send_sse({"type": "done", "conversation_id": conversation_id, "message_id": message["id"], "timings": timings})
        except (BrokenPipeError, ConnectionResetError):
            print("Streaming client disconnected", file=sys.stderr)
        except Exception as exc:
            print(f"Streaming chat failed: {exc}", file=sys.stderr)
            try:
                self._send_sse({"type": "error", "error": str(exc)})
            except Exception:
                pass

    def _send_sse(self, data: dict[str, Any]) -> None:
        payload = f"data: {json.dumps(data)}\n\n".encode("utf-8")
        self.wfile.write(payload)
        self.wfile.flush()

    def _regenerate(self, conversation_id: str, message_id: str) -> None:
        try:
            conversation = DATABASE.get_conversation(conversation_id)
            if conversation is None:
                self._send_json({"error": "Conversation not found."}, HTTPStatus.NOT_FOUND)
                return
            messages = conversation.get("messages", [])
            index = next((i for i, item in enumerate(messages) if item["id"] == message_id), -1)
            if index < 1 or messages[index].get("role") != "assistant":
                self._send_json({"error": "Assistant message not found."}, HTTPStatus.NOT_FOUND)
                return
            question = next(
                (item["content"] for item in reversed(messages[:index]) if item.get("role") == "user"),
                "",
            )
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            self._send_sse({"type": "start", "conversation_id": conversation_id, "message_id": message_id})
            answer_parts: list[str] = []
            sources: list[dict[str, Any]] = []
            for event in SERVICE.stream_answer(question):
                if event["type"] == "token":
                    answer_parts.append(event["token"])
                elif event["type"] == "sources":
                    sources = event["sources"]
                self._send_sse(event)
            message = DATABASE.add_message_version(
                conversation_id, message_id, "".join(answer_parts).strip(), sources
            )
            self._send_sse({"type": "done", "message": message})
        except Exception as exc:
            print(f"Regeneration failed: {exc}", file=sys.stderr)
            try:
                self._send_sse({"type": "error", "error": str(exc)})
            except Exception:
                pass

    def _save_feedback(self, conversation_id: str, message_id: str) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            rating = str(payload.get("rating", ""))
            if rating not in {"up", "down"}:
                self._send_json({"error": "Rating must be 'up' or 'down'."}, HTTPStatus.BAD_REQUEST)
                return
            reasons = [str(reason)[:80] for reason in payload.get("reasons", [])][:8]
            comment = str(payload.get("comment", "")).strip()[:1000]
            feedback = DATABASE.set_feedback(conversation_id, message_id, rating, reasons, comment)
            self._send_json({"feedback": feedback})
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid request body."}, HTTPStatus.BAD_REQUEST)
        except KeyError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/conversations/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        conversation_id = path.rsplit("/", 1)[-1]
        if DATABASE.delete_conversation(conversation_id):
            self._send_json({"deleted": True})
        else:
            self._send_json({"error": "Conversation not found."}, HTTPStatus.NOT_FOUND)

    def _create_conversation(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send_json({"conversation": DATABASE.create_conversation(str(payload.get("title", "New conversation")))}, HTTPStatus.CREATED)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid request body."}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"error": "Database operation failed.", "detail": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _send_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CIS Controls RAG chat UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--lazy", action="store_true", help="Initialize the RAG pipeline on the first question.")
    args = parser.parse_args()

    if not args.lazy:
        print("Preparing the RAG pipeline before opening the app...")
        SERVICE.initialize()

    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    url = f"http://{args.host}:{args.port}"
    public_ui_url = os.getenv("PUBLIC_UI_URL", "http://localhost:5127")
    print(f"CIS Controls RAG API is running at {url}")
    print(f"Open the authenticated UI at {public_ui_url}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(public_ui_url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
        SERVICE.close()
        DATABASE.close()


if __name__ == "__main__":
    main()
