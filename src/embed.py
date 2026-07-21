from __future__ import annotations

import os
import pickle
from pathlib import Path

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"

CHUNK_CACHE = CACHE_DIR / "structure_chunks.pkl"
EMBED_CACHE = CACHE_DIR / "embedded_chunks.pkl"

MODEL_NAME = "embeddinggemma"
BATCH_SIZE = 16


def get_windows_host() -> str:
    gateway = os.popen(
        "ip route show | grep -i default | awk '{ print $3 }'"
    ).read().strip()

    if not gateway:
        raise RuntimeError("Could not detect Windows host IP")

    return gateway


def load_chunks() -> list[Document]:
    if not CHUNK_CACHE.exists():
        raise FileNotFoundError(
            f"Chunk cache not found: {CHUNK_CACHE}"
        )

    with CHUNK_CACHE.open("rb") as file:
        chunks = pickle.load(file)

    print(f"Loaded chunks: {len(chunks)}")

    return chunks


def load_checkpoint() -> list[dict]:
    if not EMBED_CACHE.exists():
        return []

    print("Loading embedding checkpoint...")

    with EMBED_CACHE.open("rb") as file:
        embedded_data = pickle.load(file)

    print(
        f"Already embedded: {len(embedded_data)} chunks"
    )

    return embedded_data


def save_checkpoint(
    embedded_data: list[dict],
) -> None:
    with EMBED_CACHE.open("wb") as file:
        pickle.dump(
            embedded_data,
            file,
        )


def create_embedding_model() -> OllamaEmbeddings:
    windows_host = get_windows_host()

    base_url = (
        f"http://{windows_host}:11434"
    )

    print(f"Ollama URL: {base_url}")
    print(f"Model: {MODEL_NAME}")

    return OllamaEmbeddings(
        model=MODEL_NAME,
        base_url=base_url,
    )


def embed_chunks(
    chunks: list[Document],
    embedding_model: OllamaEmbeddings,
) -> list[dict]:
    embedded_data = load_checkpoint()

    start_index = len(embedded_data)

    if start_index >= len(chunks):
        print("All chunks are already embedded")
        return embedded_data

    print(
        f"\nResuming from chunk {start_index + 1}"
    )

    for batch_start in range(
        start_index,
        len(chunks),
        BATCH_SIZE,
    ):
        batch_end = min(
            batch_start + BATCH_SIZE,
            len(chunks),
        )

        batch = chunks[
            batch_start:batch_end
        ]

        texts = [
            chunk.page_content
            for chunk in batch
        ]

        print(
            f"Embedding chunks "
            f"{batch_start + 1}-{batch_end} "
            f"/ {len(chunks)}"
        )

        vectors = embedding_model.embed_documents(
            texts
        )

        for chunk, vector in zip(
            batch,
            vectors,
            strict=True,
        ):
            embedded_data.append(
                {
                    "document": chunk,
                    "embedding": vector,
                }
            )

        save_checkpoint(embedded_data)

        print(
            f"Checkpoint saved: "
            f"{len(embedded_data)} / {len(chunks)}"
        )

    return embedded_data


def inspect_embeddings(
    embedded_data: list[dict],
) -> None:
    if not embedded_data:
        print("No embeddings generated")
        return

    first_vector = embedded_data[0]["embedding"]

    print("\n" + "=" * 80)
    print("EMBEDDING RESULTS")
    print("=" * 80)

    print(
        f"Embedded chunks: {len(embedded_data)}"
    )

    print(
        f"Vector dimensions: {len(first_vector)}"
    )

    print(
        f"First vector preview: "
        f"{first_vector[:10]}"
    )


def main() -> None:
    chunks = load_chunks()

    embedding_model = create_embedding_model()

    embedded_data = embed_chunks(
        chunks,
        embedding_model,
    )

    inspect_embeddings(
        embedded_data
    )


if __name__ == "__main__":
    main()