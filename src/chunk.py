from __future__ import annotations

import pickle
from pathlib import Path
from statistics import mean

from langchain_core.documents import Document


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"


# --------------------------------------------------
# LOAD CLEANED DOCUMENTS
# --------------------------------------------------


def find_clean_cache() -> Path:
    cache_files = list(CACHE_DIR.glob("*_cleaned.pkl"))

    if not cache_files:
        raise FileNotFoundError(
            f"No cleaned cache found in: {CACHE_DIR}"
        )

    return cache_files[0]


def load_clean_documents(
    cache_path: Path,
) -> list[Document]:
    print(f"Loading cleaned cache: {cache_path.name}")

    with cache_path.open("rb") as file:
        documents = pickle.load(file)

    print(f"Loaded cleaned elements: {len(documents)}")

    return documents


# --------------------------------------------------
# STRUCTURE-AWARE CHUNKING
# --------------------------------------------------


def chunk_by_structure(
    documents: list[Document],
    max_characters: int = 1500,
) -> list[Document]:
    print("\nRunning structure-aware chunking...")

    chunks: list[Document] = []

    current_parts: list[str] = []
    current_metadata: dict = {}
    current_length = 0


    def flush_chunk() -> None:
        nonlocal current_parts
        nonlocal current_metadata
        nonlocal current_length

        if not current_parts:
            return

        text = "\n\n".join(current_parts).strip()

        if text:
            chunks.append(
                Document(
                    page_content=text,
                    metadata=current_metadata.copy(),
                )
            )

        current_parts = []
        current_metadata = {}
        current_length = 0


    for document in documents:
        text = document.page_content.strip()

        if not text:
            continue

        category = document.metadata.get("category")
        page_number = document.metadata.get("page_number")


        # ------------------------------------------
        # TITLE STARTS NEW SECTION
        # ------------------------------------------

        if category == "Title":
            flush_chunk()

            current_metadata = {
                "page_number": page_number,
                "source": document.metadata.get("source"),
                "filename": document.metadata.get("filename"),
                "section_title": text,
                "chunk_strategy": "structure",
            }


        # ------------------------------------------
        # SIZE LIMIT
        # ------------------------------------------

        elif (
            current_parts
            and current_length + len(text) > max_characters
        ):
            previous_metadata = current_metadata.copy()

            flush_chunk()

            current_metadata = previous_metadata


        # ------------------------------------------
        # DEFAULT METADATA
        # ------------------------------------------

        if not current_metadata:
            current_metadata = {
                "page_number": page_number,
                "source": document.metadata.get("source"),
                "filename": document.metadata.get("filename"),
                "chunk_strategy": "structure",
            }


        current_parts.append(text)

        current_length += len(text) + 2


    flush_chunk()

    print(f"Structure chunks: {len(chunks)}")

    return chunks


# --------------------------------------------------
# INSPECT CHUNKS
# --------------------------------------------------


def inspect_chunks(
    chunks: list[Document],
) -> None:
    lengths = [
        len(chunk.page_content)
        for chunk in chunks
    ]

    print("\n" + "=" * 80)
    print("STRUCTURE CHUNKING")
    print("=" * 80)

    print(f"Chunks: {len(chunks)}")
    print(f"Average characters: {mean(lengths):.2f}")
    print(f"Minimum characters: {min(lengths)}")
    print(f"Maximum characters: {max(lengths)}")


def preview_chunks(
    chunks: list[Document],
    limit: int = 10,
) -> None:
    print("\n" + "#" * 80)
    print("CHUNK PREVIEW")
    print("#" * 80)

    for index, chunk in enumerate(chunks[:limit]):
        print("\n" + "-" * 80)
        print(f"CHUNK {index + 1}")
        print("-" * 80)

        print("Page:", chunk.metadata.get("page_number"))

        print(
            "Section:",
            chunk.metadata.get(
                "section_title",
                "No section title",
            ),
        )

        print("\nContent:")
        print(chunk.page_content[:1500])


# --------------------------------------------------
# SAVE
# --------------------------------------------------


def save_chunks(
    chunks: list[Document],
) -> None:
    cache_path = CACHE_DIR / "structure_chunks.pkl"

    print(f"\nSaving: {cache_path.name}")

    with cache_path.open("wb") as file:
        pickle.dump(chunks, file)

    print("Saved successfully")


# --------------------------------------------------
# MAIN
# --------------------------------------------------


def main() -> None:
    clean_cache_path = find_clean_cache()

    documents = load_clean_documents(
        clean_cache_path
    )

    chunks = chunk_by_structure(
        documents,
        max_characters=1500,
    )

    inspect_chunks(chunks)

    preview_chunks(chunks)

    save_chunks(chunks)


if __name__ == "__main__":
    main()