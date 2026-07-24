# RAG Setup — Internal Ship Program

Starter project for the **Internal Ship Program** RAG track. It gives you a ready-to-run
environment for building a Retrieval-Augmented Generation (RAG) system with the
**LangChain ecosystem** and **local open-source models** — no API keys, your data never
leaves the machine.

The teaching notebook walks through the **ingestion** half of a RAG pipeline on a real
document (CIS Controls v8) across four stages:

```
PDF → 2.1 Parse → 2.2 Chunk → 2.3 Embed → 2.4 Store → (later: retrieve → rerank → agent)
        unstructured   splitters   bge-small   Weaviate
```

| Stage | What it does | Tool |
|-------|--------------|------|
| **2.1 Parse** | Extract text, tables, and images from the PDF | `langchain-unstructured` (`hi_res`) |
| **2.2 Chunk** | Split into retrieval-sized pieces (char / token / by-title) | `langchain-text-splitters` |
| **2.3 Embed** | Turn chunks into vectors, locally on CPU | `BAAI/bge-small-en-v1.5` |
| **2.4 Store** | Save vectors in a DB you can search by similarity | `langchain-weaviate` + Weaviate |

## Prerequisites

Make sure the following are installed **before** you start.

### 1. Python 3.12+

This project requires Python **3.12 or newer** (see `requires-python` in `pyproject.toml`).

### 2. uv (Python package/environment manager)

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Install it once:

```bash
# Linux / macOS / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh
```

uv reads `pyproject.toml` + `uv.lock` and creates an isolated `.venv` for you — you don't
need to manage virtualenvs or `pip` by hand.

### 3. System packages for hi-res PDF parsing

`unstructured` uses OCR and a layout model to detect tables and images. Install these
system libraries (Debian / Ubuntu / WSL):

```bash
sudo apt-get update && sudo apt-get install -y poppler-utils tesseract-ocr libgl1
```

| Package | Why it's needed |
|---------|-----------------|
| `poppler-utils` | renders PDF pages to images |
| `tesseract-ocr` | reads text from those images (OCR) |
| `libgl1` | shared library the layout/vision model needs |

> On macOS use Homebrew instead: `brew install poppler tesseract`.

### 4. Docker (for Weaviate, recommended)

The vector database stage uses **Weaviate**. Running it in Docker is the recommended path
(an embedded fallback exists, but Docker is more reliable). Install
[Docker](https://docs.docker.com/get-docker/), then start Weaviate:

```bash
docker run -p 8080:8080 -p 50051:50051 cr.weaviate.io/semitechnologies/weaviate:1.27.0
```

## Setup

From the `rag_setup/` directory:

```bash
# 1. Install Python dependencies into an isolated .venv
uv sync

# 2. Launch Jupyter
uv run jupyter lab        # or: uv run jupyter notebook
```

Open [`notebooks/01_RAG_setup.ipynb`](notebooks/01_RAG_setup.ipynb), select this project's
`.venv` as the kernel, and run the cells top to bottom.

## Run the authenticated chat application

The application has three processes. Keep each command running in its own terminal.

1. In WSL, configure `.env`, make Ollama reachable from WSL, and start the Python RAG API:

```bash
WINDOWS_HOST_IP=$(ip route show | awk '/default/ { print $3 }')
curl "http://${WINDOWS_HOST_IP}:11434/api/tags"
uv run python main.py --host 0.0.0.0 --no-browser
```

If the `curl` command times out, Ollama on Windows is listening only on localhost. Set
the Windows user environment variable `OLLAMA_HOST` to `0.0.0.0:11434`, restart Ollama,
then put these values in `.env` (replace the placeholder with the address printed by
`ip route show`):

```dotenv
OLLAMA_BASE_URL=http://WINDOWS_HOST_IP:11434
WEAVIATE_HOST=WINDOWS_HOST_IP
```

2. In PowerShell, start the protected .NET middleware:

```powershell
dotnet run --project RagMiddleware/src/RagMiddleware.Api
```

3. Build the React UI once (or whenever frontend code changes):

```powershell
cd frontend
pnpm install
pnpm run build
```

Open `http://localhost:5127`. The middleware serves the production React build. Port
`8000` is the internal Python API and redirects browser visits to the public UI.

For frontend development with hot reload, run `pnpm run dev` and open
`http://localhost:5173` instead. The middleware also requires MongoDB, Google OAuth,
and JWT settings described in `RagMiddleware/README.md`.

> **First run is slow (one-time):** it downloads the embedding model (~130 MB) and the
> layout model, and `hi_res` parsing of the full PDF takes a few minutes on CPU. Everything
> is cached afterward.

## Project layout

```
rag_setup/
├── data/                        # CIS Controls v8 PDF (sample document)
├── notebooks/
│   └── 01_RAG_setup.ipynb       # ingestion pipeline walkthrough (Tasks 2.1 → 2.4)
├── main.py                      # placeholder entry point
├── pyproject.toml               # dependencies + Python version
└── uv.lock                      # pinned dependency versions
```
