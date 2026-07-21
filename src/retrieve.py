from __future__ import annotations

from pipeline import RAGPipeline


def display_sources(
    result: dict,
) -> None:
    sources = result.get(
        "reranked_sources",
        [],
    )

    print("\n" + "=" * 80)
    print("RERANKED SOURCES")
    print("=" * 80)

    if not sources:
        print(
            "No source passed the "
            "reranker threshold."
        )
        return

    for index, source in enumerate(
        sources,
        start=1,
    ):
        print("\n" + "-" * 80)
        print(f"SOURCE {index}")
        print("-" * 80)

        print(
            "BGE score:",
            source.get("bge_score"),
        )

        print(
            "Hybrid score:",
            source.get("hybrid_score"),
        )

        print(
            "Page:",
            source.get("page_number"),
        )

        print(
            "Section:",
            source.get("section_title"),
        )

        print("\nContent:\n")
        print(
            source.get("content", "")
        )


def main() -> None:
    question = input(
        "Enter your CIS Controls question: "
    ).strip()

    if not question:
        print("Question cannot be empty.")
        return

    with RAGPipeline() as pipeline:
        result = pipeline.answer(
            question
        )

        display_sources(result)

        print("\n" + "=" * 80)
        print("FINAL ANSWER")
        print("=" * 80)
        print(result["answer"])

        print("\n" + "=" * 80)
        print("TIMING")
        print("=" * 80)

        for name, seconds in (
            result["timings"].items()
        ):
            print(
                f"{name}: {seconds:.2f}s"
            )


if __name__ == "__main__":
    main()