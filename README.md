# CIS Controls RAG Assistant

An authenticated, local-first Retrieval-Augmented Generation (RAG) assistant for the
CIS Critical Security Controls v8. Users sign in with Google, ask security questions,
receive streamed answers grounded in the indexed CIS document, inspect citations,
regenerate answers, submit feedback, and resume saved conversations.

## What is included

- Local RAG pipeline using Ollama, Weaviate, LangChain, and reranked retrieval
- Streaming Server-Sent Events (SSE) responses
- React 19 interface with Markdown rendering and accessible controls
- Google OAuth through an ASP.NET Core 8 middleware
- HTTP-only JWT authentication cookies
- MongoDB conversation, user, audit-log, version, and feedback persistence
- Inline citation previews and expandable source metadata
- Answer regeneration and version switching
- First-run spotlight tour
- Unit, end-to-end, and accessibility tests

## Architecture

```mermaid
flowchart LR
    Browser["React UI"] -->|"Google sign-in + API requests"| Middleware["ASP.NET Core middleware :5127"]
    Middleware -->|"Protected proxy + SSE"| Python["Python RAG API :8000"]
    Middleware -->|"Users + audit logs"| Mongo["MongoDB"]
    Python -->|"Conversations + feedback"| Mongo
    Python -->|"Hybrid retrieval"| Weaviate["Weaviate :8080 / :50051"]
    Python -->|"Embeddings + generation"| Ollama["Ollama :11434"]
```

The browser communicates only with the middleware. RAG service credentials, Google
OAuth secrets, MongoDB credentials, and model connections remain server-side.

## Prerequisites

Install these once:

- Git
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20.19+ and [pnpm](https://pnpm.io/installation)
- [.NET SDK 8](https://dotnet.microsoft.com/download/dotnet/8.0)
- [Ollama](https://ollama.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Weaviate
- MongoDB Community Server or a MongoDB Atlas cluster
- A Google Cloud OAuth 2.0 **Web application** client

The commands below use WSL for Python and PowerShell for .NET and React. macOS and
Linux users can run the equivalent commands in separate terminals.

## Five-minute quickstart

This quickstart assumes the prerequisites are installed and the `CISControls`
Weaviate collection has already been populated. For a brand-new vector database, see
[First-time document indexing](#first-time-document-indexing).

### 1. Clone and install

```bash
git clone https://github.com/Mohamad-jaber750/RAG-SETUP.git
cd RAG-SETUP
cp .env.example .env
uv sync
cd frontend
pnpm install
pnpm run build
cd ..
```

Edit `.env`:

```dotenv
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=rag_assistant
OLLAMA_BASE_URL=http://WINDOWS_HOST_IP:11434
WEAVIATE_HOST=WINDOWS_HOST_IP
PUBLIC_UI_URL=http://localhost:5127
```

When Ollama and Weaviate run on the same Linux/macOS host as Python, use:

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
WEAVIATE_HOST=localhost
```

In WSL, obtain the Windows host address with:

```bash
ip route show | awk '/default/ { print $3 }'
```

### 2. Start local model and vector services

Pull the required Ollama models:

```bash
ollama pull embeddinggemma
ollama pull qwen3:1.7b
```

Start Weaviate:

```bash
docker run --name cis-weaviate --rm \
  -p 8080:8080 -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:1.27.0
```

If Ollama runs on Windows while Python runs in WSL, set the Windows user environment
variable `OLLAMA_HOST=0.0.0.0:11434`, then restart Ollama.

### 3. Configure Google OAuth and middleware secrets

In Google Cloud Console, add this authorized redirect URI to the Web application
OAuth client:

```text
http://localhost:5127/signin-google
```

From the repository root in PowerShell:

```powershell
dotnet user-secrets set "Authentication:Google:ClientId" "YOUR_CLIENT_ID" --project RagMiddleware/src/RagMiddleware.Api
dotnet user-secrets set "Authentication:Google:ClientSecret" "YOUR_CLIENT_SECRET" --project RagMiddleware/src/RagMiddleware.Api
dotnet user-secrets set "Jwt:SigningKey" "REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS" --project RagMiddleware/src/RagMiddleware.Api
dotnet user-secrets set "MongoDb:ConnectionString" "YOUR_MONGODB_URI" --project RagMiddleware/src/RagMiddleware.Api
dotnet user-secrets set "MongoDb:DatabaseName" "rag_middleware" --project RagMiddleware/src/RagMiddleware.Api
dotnet user-secrets set "RagApi:BaseUrl" "http://127.0.0.1:8000" --project RagMiddleware/src/RagMiddleware.Api
```

Do not place real credentials in `appsettings.json` or commit `.env`.

### 4. Run the full stack

Terminal 1 — Python RAG API:

```bash
uv run python main.py --host 0.0.0.0 --no-browser
```

Terminal 2 — authenticated middleware and production UI:

```powershell
dotnet run --project RagMiddleware/src/RagMiddleware.Api
```

Open [http://localhost:5127](http://localhost:5127), sign in with Google, and ask a
question such as:

> What are the first steps to establish an asset inventory?

## First-time document indexing

Skip this section if startup reports that the `CISControls` collection already contains
objects.

On Debian, Ubuntu, or WSL, install the PDF parsing dependencies:

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr libgl1
```

Make sure Weaviate and Ollama are running, then execute:

```bash
uv run python src/parse.py
uv run python src/chunk.py
uv run python src/embed.py
uv run python src/store.py
```

The source PDF is located at:

```text
data/CIS_Controls__v8__Critical_Security_Controls__2023_08.pdf
```

Initial parsing and model downloads can take several minutes. Subsequent launches reuse
the generated caches and local model files.

## Using the application

1. Sign in with Google.
2. Follow or skip the first-run guided tour.
3. Start a new conversation and submit a CIS Controls question.
4. Watch the answer stream into the interface.
5. Hover or focus citation badges such as `[1]` to inspect their source passages.
6. Expand the source metadata section for full citation details.
7. Regenerate the answer and switch between saved versions.
8. Submit thumbs-up or thumbs-down feedback with optional reasons and comments.
9. Reload the page and resume the saved conversation from the sidebar.

The `?` button in the bottom-right corner restarts the guided tour.

## Development mode

Run the React development server:

```bash
cd frontend
pnpm run dev
```

Open [http://localhost:5173](http://localhost:5173). API requests are proxied to the
middleware at `http://localhost:5127`.

For an authentication-free UI preview:

```text
http://localhost:5127/?preview=true
```

Preview mode is for visual development only; it does not exercise the protected API.

## Validation

Frontend quality checks:

```bash
cd frontend
pnpm run lint
pnpm run format:check
pnpm test
pnpm run build
pnpm run test:e2e
```

Middleware build:

```powershell
dotnet build RagMiddleware/src/RagMiddleware.Api/RagMiddleware.Api.csproj
```

Python syntax check:

```bash
uv run python -m py_compile main.py src/*.py
```

Health checks:

```text
Python API: http://127.0.0.1:8000/api/health
Middleware: http://localhost:5127/api/health
Swagger:    http://localhost:5127/swagger
```

## Project structure

```text
.
|-- data/                         CIS Controls v8 source document
|-- docs/                         MongoDB schema documentation
|-- evaluation/                   Evaluation datasets and results
|-- frontend/                     React/Vite application and tests
|-- notebooks/                    RAG ingestion walkthrough
|-- RagMiddleware/                ASP.NET Core authentication and proxy layer
|-- src/                          Parsing, retrieval, generation, and persistence
|-- .github/copilot-instructions.md
|-- AI_TOOLING.md                 AI tooling usage guide
|-- main.py                       Python HTTP and streaming API
|-- pyproject.toml                Python project definition
`-- uv.lock                       Locked Python dependencies
```

## Key API routes

All browser-facing routes are served through the authenticated middleware.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/auth/me` | Return the signed-in user |
| `GET` | `/api/auth/login/google` | Start Google OAuth |
| `POST` | `/api/auth/logout` | Clear the authentication cookie |
| `POST` | `/api/chat/stream` | Stream a grounded answer |
| `GET` | `/api/conversations` | List saved conversations |
| `GET` | `/api/conversations/{id}` | Load a conversation |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation |
| `POST` | `/api/conversations/{id}/messages/{messageId}/regenerate` | Regenerate an answer |
| `POST` | `/api/conversations/{id}/messages/{messageId}/feedback` | Save feedback |

## Troubleshooting

### `Authentication API unavailable` or `Failed to fetch`

- Open the UI at `http://localhost:5127`, not port `8000`.
- Confirm the .NET middleware is running.
- Rebuild the frontend with `pnpm run build` after UI changes.

### Google reports `redirect_uri_mismatch`

The Google OAuth client must contain exactly:

```text
http://localhost:5127/signin-google
```

### Python reports `Conversation not found`

Reload the page and start a new conversation. Confirm `MONGODB_URI` points to the same
database used when the conversation was created.

### The RAG service cannot reach Ollama or Weaviate

From WSL:

```bash
WINDOWS_HOST_IP=$(ip route show | awk '/default/ { print $3 }')
curl "http://${WINDOWS_HOST_IP}:11434/api/tags"
curl "http://${WINDOWS_HOST_IP}:8080/v1/.well-known/ready"
```

Check `OLLAMA_BASE_URL` and `WEAVIATE_HOST` in `.env`, Windows firewall access, and the
`OLLAMA_HOST` setting.

### The `CISControls` collection is missing or empty

Run the four commands in [First-time document indexing](#first-time-document-indexing).

More middleware recovery steps are available in
[`RagMiddleware/RUNBOOK.md`](RagMiddleware/RUNBOOK.md).

## Security notes

- Real secrets are ignored by Git and must stay in `.env`, .NET User Secrets, environment
  variables, or a production secret manager.
- Authentication tokens are stored in HTTP-only cookies.
- The React application never receives RAG service credentials.
- Middleware errors are sanitized before being returned to the browser.
- Audit logs store request metadata, not authentication tokens or full prompts.

## AI tooling

Repository-specific GitHub Copilot instructions are checked in at
[`/.github/copilot-instructions.md`](.github/copilot-instructions.md). The accompanying
[`AI_TOOLING.md`](AI_TOOLING.md) explains how AI assistance was used, its development
impact, privacy constraints, and required human review.

## Branches

Major work is preserved on dedicated branches:

- `feature/frontend-chat-ui`
- `feature/backend-integration`
- `feature/mongodb-persistence`
- `feature/middleware`
- `feature/sse-streaming`
- `feature/ai-tooling`

The complete, reviewed application is available on `main`.

## License and source material

This repository is an educational/internal delivery project. Review the applicable CIS
Controls licensing terms before redistributing the included source document.
