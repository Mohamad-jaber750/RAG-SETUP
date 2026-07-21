from pathlib import Path
import pickle
from clean import (
    clean_documents,
    inspect_categories,
    save_clean_cache,
)
from langchain_unstructured import UnstructuredLoader


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / "cache"

CACHE_DIR.mkdir(exist_ok=True)


def find_pdf() -> Path:
    pdf_files = list(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {DATA_DIR}"
        )

    return pdf_files[0]


def get_cache_path(pdf_path: Path) -> Path:
    return CACHE_DIR / f"{pdf_path.stem}_parsed.pkl"


def load_cache(cache_path: Path):
    if not cache_path.exists():
        return None

    print(f"Loading cached parse: {cache_path.name}")

    with cache_path.open("rb") as file:
        documents = pickle.load(file)

    print(f"Loaded {len(documents)} cached elements")

    return documents


def save_cache(documents, cache_path: Path) -> None:
    print(f"Saving parse cache: {cache_path.name}")

    with cache_path.open("wb") as file:
        pickle.dump(documents, file)

    print("Cache saved successfully")


def parse_pdf(pdf_path: Path):
    print(f"Parsing: {pdf_path.name}")

    loader = UnstructuredLoader(
        file_path=str(pdf_path),
        strategy="hi_res",
    )

    documents = loader.load()

    print(f"Parsed elements: {len(documents)}")

    return documents


def get_documents(pdf_path: Path):
    cache_path = get_cache_path(pdf_path)

    cached_documents = load_cache(cache_path)

    if cached_documents is not None:
        return cached_documents

    documents = parse_pdf(pdf_path)

    save_cache(documents, cache_path)

    return documents


def display_documents(documents, limit: int = 10) -> None:
    for index, document in enumerate(documents[:limit]):
        print("=" * 80)
        print(f"Element: {index}")
        print("Category:", document.metadata.get("category"))
        print("Page:", document.metadata.get("page_number"))
        print()

        print(document.page_content[:500])

        print()


def main() -> None:
    pdf_path = find_pdf()

    documents = get_documents(pdf_path)

    inspect_categories(documents)

    cleaned_documents = clean_documents(documents)

    inspect_categories(cleaned_documents)

    clean_cache_path = (
        CACHE_DIR / f"{pdf_path.stem}_cleaned.pkl"
    )

    save_clean_cache(
        cleaned_documents,
        clean_cache_path,
    )

    display_documents(cleaned_documents)


if __name__ == "__main__":
    main()