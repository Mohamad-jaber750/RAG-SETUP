from __future__ import annotations

import os
from typing import Any

# Force Hugging Face to use the already downloaded model.
# These lines must appear before importing sentence_transformers.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import CrossEncoder


RERANKER_MODEL = "BAAI/bge-reranker-base"
MIN_SCORE = 0.20


class BGEReranker:
    def __init__(self) -> None:
        print(f"Loading reranker: {RERANKER_MODEL}")

        self.model = CrossEncoder(
            RERANKER_MODEL,
            device="cpu",
        )

        print("BGE reranker ready")

    def rerank(
        self,
        question: str,
        retrieved_objects: list[Any],
        top_n: int = 5,
    ) -> list[tuple[Any, float]]:
        if not retrieved_objects:
            return []

        pairs: list[list[str]] = []

        for obj in retrieved_objects:
            content = obj.properties.get("content", "")

            if not isinstance(content, str):
                content = str(content)

            pairs.append(
                [
                    question,
                    content,
                ]
            )

        print(
            f"Reranking {len(pairs)} retrieved chunks..."
        )

        scores = self.model.predict(
            pairs,
            batch_size=4,
            show_progress_bar=False,
        )

        ranked_results = sorted(
            zip(retrieved_objects, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        filtered_results = [
            (obj, float(score))
            for obj, score in ranked_results
            if float(score) >= MIN_SCORE
        ]

        keep_count = min(
            top_n,
            len(filtered_results),
        )

        print(
            f"Keeping {keep_count} chunks "
            f"with BGE score >= {MIN_SCORE}"
        )

        return filtered_results[:keep_count]