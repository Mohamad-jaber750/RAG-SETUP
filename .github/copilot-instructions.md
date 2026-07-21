# RAG Setup — AI coding instructions

## Project purpose

This repository implements a local retrieval-augmented generation assistant for the
CIS Critical Security Controls v8. Keep document data and inference local; do not add
hosted model APIs or telemetry unless the user explicitly requests them.

## Architecture

- `src/` contains parsing, chunking, embedding, storage, retrieval, reranking, generation,
  and evaluation modules.
- `src/pipeline.py` is the orchestration boundary. Prefer calling `RAGPipeline.answer()`
  rather than duplicating retrieval or generation logic.
- `main.py` is the application entry point. Backend API work belongs on the
  `feature/backend-integration` branch.
- `frontend/` is a React/Vite client. Frontend work belongs on the
  `feature/frontend-chat-ui` branch.
- Weaviate stores document vectors. Ollama provides embeddings and answer generation.

## Development rules

1. Preserve local-first operation and never commit secrets, virtual environments,
   package caches, model weights, or `node_modules`.
2. Keep retrieval results grounded in the indexed document. Do not silently add outside
   knowledge to generated answers.
3. Reuse existing modules and constants before introducing a parallel implementation.
4. Keep React components focused and place network calls in `frontend/src/services/`.
5. Include accessible labels, keyboard behavior, loading states, and error states in UI work.
6. Add dependencies only when the standard library or an existing dependency cannot
   reasonably satisfy the requirement.
7. Make descriptive commits on feature branches. Do not merge or push feature work
   directly to `main`.

## Validation

- Python syntax: `uv run python -m py_compile main.py src/*.py`
- Backend: verify `GET /api/health` and request validation on `POST /api/chat`.
- Frontend install: `cd frontend && pnpm install`
- Frontend build: `cd frontend && pnpm run build`
- Full RAG answers require Ollama, Weaviate, and the populated `CISControls` collection.

## Using these instructions

GitHub Copilot automatically reads this file when operating in the repository. Give it a
specific task and name the target feature branch. Ask it to report the files changed and
validation performed. Review generated changes before committing, especially retrieval
settings, prompts, dependency files, and anything that can expose local data.
