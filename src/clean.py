import re
from collections import Counter
from pathlib import Path
import pickle

from langchain_core.documents import Document

def save_clean_cache(documents, cache_path: Path) -> None:
    print(f"Saving cleaned cache: {cache_path.name}")

    with cache_path.open("wb") as file:
        pickle.dump(documents, file)

    print("Cleaned cache saved successfully")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"


def inspect_categories(documents):
    categories = Counter(
        document.metadata.get("category", "Unknown")
        for document in documents
    )

    print("\nELEMENT CATEGORIES")
    print("=" * 80)

    for category, count in categories.most_common():
        print(f"{category}: {count}")

def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n[ \t]+", "\n", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_empty_documents(documents):
    return [
        document
        for document in documents
        if document.page_content.strip()
    ]


def normalize_documents(documents):
    cleaned_documents = []

    for document in documents:
        cleaned_text = normalize_whitespace(
            document.page_content
        )

        if not cleaned_text:
            continue

        cleaned_document = Document(
            page_content=cleaned_text,
            metadata=document.metadata.copy(),
        )

        cleaned_documents.append(cleaned_document)

    return cleaned_documents

def remove_exact_duplicates(documents):
    seen = set()
    unique_documents = []

    for document in documents:
        text = document.page_content.strip()
        page_number = document.metadata.get("page_number")
        category = document.metadata.get("category")

        duplicate_key = (
            text,
            page_number,
            category,
        )

        if duplicate_key in seen:
            continue

        seen.add(duplicate_key)
        unique_documents.append(document)

    return unique_documents


def clean_documents(documents):
    original_count = len(documents)

    print("\nCleaning documents...")
    print(f"Raw elements: {original_count}")

    documents = remove_empty_documents(documents)

    after_empty = len(documents)

    print(
        f"After removing empty elements: {after_empty}"
    )

    documents = normalize_documents(documents)

    after_normalization = len(documents)

    print(
        f"After whitespace normalization: "
        f"{after_normalization}"
    )

    documents = remove_exact_duplicates(documents)

    final_count = len(documents)

    print(
        f"After duplicate removal: {final_count}"
    )

    removed_count = original_count - final_count

    print(f"Removed elements: {removed_count}")

    return documents