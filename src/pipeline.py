from __future__ import annotations

import subprocess
import time
from typing import Any

import weaviate
from langchain_ollama import OllamaEmbeddings
from weaviate.classes.init import (
    AdditionalConfig,
    Timeout,
)
from weaviate.classes.query import MetadataQuery

from generate import QwenGenerator
from rerank import BGEReranker


COLLECTION_NAME = "CISControls"
EMBEDDING_MODEL = "embeddinggemma"

RETRIEVAL_TOP_K = 20
RERANK_TOP_K = 3


EXPECTED_VECTOR_DIMENSIONS = 768
HYBRID_ALPHA = 0.5


class RAGPipeline:
    def __init__(self) -> None:
        self.windows_host = (
            self._get_windows_host()
        )

        self.ollama_url = (
            f"http://{self.windows_host}:11434"
        )

        self.embedding_model = (
            OllamaEmbeddings(
                model=EMBEDDING_MODEL,
                base_url=self.ollama_url,
            )
        )

        self.client = (
            self._connect_to_weaviate()
        )

        self.collection = (
            self._get_collection()
        )

        self._inspect_collection()

        self.target_vector = (
            self._detect_target_vector()
        )

        # These Python objects are initialized once.
        self.reranker = BGEReranker()

        self.generator = QwenGenerator(
            base_url=self.ollama_url,
        )

        print("\nRAG pipeline ready")

    # --------------------------------------------------
    # CONNECTION
    # --------------------------------------------------

    @staticmethod
    def _get_windows_host() -> str:
        result = subprocess.run(
            [
                "bash",
                "-lc",
                (
                    "ip route show "
                    "| grep -i default "
                    "| awk '{ print $3 }'"
                ),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        host = result.stdout.strip()

        if not host:
            raise RuntimeError(
                "Could not detect the Windows host IP."
            )

        return host

    def _connect_to_weaviate(self):
        print(
            "Connecting to Weaviate at "
            f"{self.windows_host}:8080"
        )

        client = weaviate.connect_to_local(
            host=self.windows_host,
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
                "Weaviate is not ready."
            )

        print("Connected to Weaviate")

        return client

    def _get_collection(self):
        if not self.client.collections.exists(
            COLLECTION_NAME
        ):
            raise RuntimeError(
                "Collection does not exist: "
                f"{COLLECTION_NAME}"
            )

        return self.client.collections.use(
            COLLECTION_NAME
        )

    def _inspect_collection(self) -> None:
        result = (
            self.collection.aggregate.over_all(
                total_count=True
            )
        )

        count = result.total_count or 0

        print(
            f"Objects in collection: {count}"
        )

        if count == 0:
            raise RuntimeError(
                "The collection is empty."
            )

    # --------------------------------------------------
    # VECTOR CONFIGURATION
    # --------------------------------------------------

    @staticmethod
    def _normalize_vector(
        vector_value: Any,
    ) -> list[float]:
        if (
            isinstance(vector_value, list)
            and vector_value
            and isinstance(
                vector_value[0],
                list,
            )
        ):
            vector_value = vector_value[0]

        if not isinstance(
            vector_value,
            list,
        ):
            raise RuntimeError(
                "Stored vector has an "
                "unexpected format."
            )

        return vector_value

    def _detect_target_vector(
        self,
    ) -> str | None:
        result = (
            self.collection.query.fetch_objects(
                limit=1,
                include_vector=True,
            )
        )

        if not result.objects:
            raise RuntimeError(
                "Could not fetch a test object."
            )

        stored_vector = (
            result.objects[0].vector
        )

        if not stored_vector:
            raise RuntimeError(
                "Stored object has no vector."
            )

        if isinstance(
            stored_vector,
            dict,
        ):
            vector_names = list(
                stored_vector.keys()
            )

            if not vector_names:
                raise RuntimeError(
                    "Named-vector dictionary "
                    "is empty."
                )

            vector_name = vector_names[0]

            vector = self._normalize_vector(
                stored_vector[vector_name]
            )

            if (
                len(vector)
                != EXPECTED_VECTOR_DIMENSIONS
            ):
                raise ValueError(
                    "Stored vector dimensions "
                    f"are {len(vector)}, expected "
                    f"{EXPECTED_VECTOR_DIMENSIONS}."
                )

            print(
                "Using named vector: "
                f"{vector_name}"
            )

            return vector_name

        vector = self._normalize_vector(
            stored_vector
        )

        if (
            len(vector)
            != EXPECTED_VECTOR_DIMENSIONS
        ):
            raise ValueError(
                "Stored vector dimensions "
                f"are {len(vector)}, expected "
                f"{EXPECTED_VECTOR_DIMENSIONS}."
            )

        print(
            "Using unnamed/default vector"
        )

        return None

    # --------------------------------------------------
    # RAG STAGES
    # --------------------------------------------------

    def _embed_question(
        self,
        question: str,
    ) -> list[float]:
        vector = (
            self.embedding_model.embed_query(
                question
            )
        )

        if (
            len(vector)
            != EXPECTED_VECTOR_DIMENSIONS
        ):
            raise ValueError(
                "Query vector dimensions "
                f"are {len(vector)}, expected "
                f"{EXPECTED_VECTOR_DIMENSIONS}."
            )

        return vector

    def _retrieve(
        self,
        question: str,
        query_vector: list[float],
    ):
        arguments: dict[str, Any] = {
            "query": question,
            "vector": query_vector,
            "alpha": HYBRID_ALPHA,
            "limit": RETRIEVAL_TOP_K,
            "return_properties": [
                "content",
                "page_number",
                "section_title",
                "filename",
                "chunk_strategy",
            ],
            "return_metadata": MetadataQuery(
                score=True,
                explain_score=True,
            ),
        }

        if self.target_vector is not None:
            arguments["target_vector"] = (
                self.target_vector
            )

        result = (
            self.collection.query.hybrid(
                **arguments
            )
        )

        return result.objects

    @staticmethod
    def _serialize_candidate(
        obj,
        bge_score: float | None = None,
    ) -> dict[str, Any]:
        properties = obj.properties

        hybrid_score = None

        if (
            obj.metadata is not None
            and obj.metadata.score is not None
        ):
            hybrid_score = float(
                obj.metadata.score
            )

        return {
            "page_number": properties.get(
                "page_number"
            ),
            "section_title": properties.get(
                "section_title"
            ),
            "filename": properties.get(
                "filename"
            ),
            "content": properties.get(
                "content",
                "",
            ),
            "hybrid_score": hybrid_score,
            "bge_score": bge_score,
        }

    # --------------------------------------------------
    # PUBLIC METHOD
    # --------------------------------------------------

    def answer(
        self,
        question: str,
    ) -> dict[str, Any]:
        total_start = time.perf_counter()

        embedding_start = time.perf_counter()

        query_vector = self._embed_question(
            question
        )

        embedding_seconds = (
            time.perf_counter()
            - embedding_start
        )

        retrieval_start = time.perf_counter()

        retrieved_objects = self._retrieve(
            question=question,
            query_vector=query_vector,
        )

        retrieval_seconds = (
            time.perf_counter()
            - retrieval_start
        )

        reranking_start = time.perf_counter()

        ranked_results = (
            self.reranker.rerank(
                question=question,
                retrieved_objects=(
                    retrieved_objects
                ),
                top_n=RERANK_TOP_K,
            )
        )

        reranking_seconds = (
            time.perf_counter()
            - reranking_start
        )

        generation_start = (
            time.perf_counter()
        )

        generated_answer = (
            self.generator.generate_answer(
                question=question,
                ranked_results=ranked_results,
            )
        )

        generation_seconds = (
            time.perf_counter()
            - generation_start
        )

        total_seconds = (
            time.perf_counter()
            - total_start
        )

        retrieved_sources = [
            self._serialize_candidate(obj)
            for obj in retrieved_objects
        ]

        reranked_sources = [
            self._serialize_candidate(
                obj,
                bge_score=float(score),
            )
            for obj, score in ranked_results
        ]

        return {
            "question": question,
            "answer": generated_answer,
            "retrieved_sources": (
                retrieved_sources
            ),
            "reranked_sources": (
                reranked_sources
            ),
            "timings": {
                "embedding_seconds": (
                    embedding_seconds
                ),
                "retrieval_seconds": (
                    retrieval_seconds
                ),
                "reranking_seconds": (
                    reranking_seconds
                ),
                "generation_seconds": (
                    generation_seconds
                ),
                "total_seconds": (
                    total_seconds
                ),
            },
        }

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            print(
                "Weaviate connection closed"
            )

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()