from __future__ import annotations

import os
import pickle
from pathlib import Path

import weaviate
from weaviate.classes.config import (
    Configure,
    DataType,
    Property,
)
from weaviate.classes.init import (
    AdditionalConfig,
    Timeout,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"

EMBED_CACHE = CACHE_DIR / "embedded_chunks.pkl"

COLLECTION_NAME = "CISControls"


# --------------------------------------------------
# WINDOWS HOST
# --------------------------------------------------


def get_windows_host() -> str:
    gateway = os.popen(
        "ip route show | grep -i default | awk '{ print $3 }'"
    ).read().strip()

    if not gateway:
        raise RuntimeError(
            "Could not detect Windows host IP"
        )

    return gateway


# --------------------------------------------------
# LOAD EMBEDDED CHUNKS
# --------------------------------------------------


def load_embedded_chunks() -> list[dict]:
    if not EMBED_CACHE.exists():
        raise FileNotFoundError(
            f"Embedding cache not found: {EMBED_CACHE}"
        )

    print(
        f"Loading embeddings: {EMBED_CACHE.name}"
    )

    with EMBED_CACHE.open("rb") as file:
        embedded_data = pickle.load(file)

    print(
        f"Loaded embedded chunks: "
        f"{len(embedded_data)}"
    )

    return embedded_data


# --------------------------------------------------
# CONNECT
# --------------------------------------------------


def connect_to_weaviate():
    windows_host = get_windows_host()

    print(
        f"Connecting to Weaviate: "
        f"{windows_host}:8080"
    )

    client = weaviate.connect_to_local(
        host=windows_host,
        port=8080,
        grpc_port=50051,
        additional_config=AdditionalConfig(
            timeout=Timeout(
                init=30,
                query=60,
                insert=120,
            )
        ),
    )

    if not client.is_ready():
        client.close()

        raise RuntimeError(
            "Weaviate is not ready"
        )

    print("Weaviate connected")

    return client


# --------------------------------------------------
# CREATE COLLECTION
# --------------------------------------------------


def create_collection(client) -> None:
    if client.collections.exists(
        COLLECTION_NAME
    ):
        print(
            f"Collection already exists: "
            f"{COLLECTION_NAME}"
        )

        return

    print(
        f"Creating collection: "
        f"{COLLECTION_NAME}"
    )

    client.collections.create(
        name=COLLECTION_NAME,

        vector_config=Configure.Vectors.self_provided(),

        properties=[
            Property(
                name="content",
                data_type=DataType.TEXT,
            ),
            Property(
                name="page_number",
                data_type=DataType.INT,
            ),
            Property(
                name="section_title",
                data_type=DataType.TEXT,
            ),
            Property(
                name="filename",
                data_type=DataType.TEXT,
            ),
            Property(
                name="chunk_strategy",
                data_type=DataType.TEXT,
            ),
        ],
    )

    print("Collection created")


# --------------------------------------------------
# CHECK EXISTING DATA
# --------------------------------------------------


def collection_has_data(collection) -> bool:
    response = collection.aggregate.over_all(
        total_count=True
    )

    count = response.total_count or 0

    print(f"Existing objects: {count}")

    return count > 0


# --------------------------------------------------
# STORE
# --------------------------------------------------


def store_embeddings(
    client,
    embedded_data: list[dict],
) -> None:
    collection = client.collections.use(
        COLLECTION_NAME
    )

    if collection_has_data(collection):
        print(
            "\nCollection already contains data."
        )
        print(
            "Skipping insertion to prevent duplicates."
        )

        return

    print(
        f"\nStoring {len(embedded_data)} chunks..."
    )

    with client.batch.fixed_size(
        batch_size=32
    ) as batch:

        for index, item in enumerate(
            embedded_data,
            start=1,
        ):
            document = item["document"]
            vector = item["embedding"]

            metadata = document.metadata

            properties = {
                "content": document.page_content,
                "page_number": (
                    metadata.get("page_number") or 0
                ),
                "section_title": (
                    metadata.get("section_title") or ""
                ),
                "filename": (
                    metadata.get("filename") or ""
                ),
                "chunk_strategy": (
                    metadata.get("chunk_strategy")
                    or "structure"
                ),
            }

            batch.add_object(
    collection=COLLECTION_NAME,
    properties=properties,
    vector={
        "default": vector,
    },
)

            if index % 32 == 0:
                print(
                    f"Queued {index} / "
                    f"{len(embedded_data)}"
                )

    failed_objects = (
        client.batch.failed_objects
    )

    if failed_objects:
        print(
            f"\nFailed objects: "
            f"{len(failed_objects)}"
        )

        for failed in failed_objects[:5]:
            print(failed)

        raise RuntimeError(
            "Some objects failed to import"
        )

    print("\nAll chunks stored successfully")


# --------------------------------------------------
# VERIFY
# --------------------------------------------------


def verify_collection(client) -> None:
    collection = client.collections.use(
        COLLECTION_NAME
    )

    response = collection.aggregate.over_all(
        total_count=True
    )

    count = response.total_count or 0

    print("\n" + "=" * 80)
    print("WEAVIATE RESULTS")
    print("=" * 80)

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Stored objects: {count}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------


def main() -> None:
    embedded_data = load_embedded_chunks()

    client = connect_to_weaviate()

    try:
        create_collection(client)

        store_embeddings(
            client,
            embedded_data,
        )

        verify_collection(client)

    finally:
        client.close()

        print("\nWeaviate connection closed")


if __name__ == "__main__":
    main()