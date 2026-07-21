from __future__ import annotations

from typing import Any

from langchain_ollama import ChatOllama


GENERATION_MODEL = "qwen3:1.7b"


class QwenGenerator:
    def __init__(
        self,
        base_url: str,
    ) -> None:
        print(
            f"Initializing generator: "
            f"{GENERATION_MODEL}"
        )

        self.model = ChatOllama(
            model=GENERATION_MODEL,
            base_url=base_url,
            temperature=0.1,
            num_ctx=4096,
        )

        print("Qwen generator ready")

    def generate_answer(
        self,
        question: str,
        ranked_results: list[tuple[Any, float]],
    ) -> str:
        if not ranked_results:
            return (
                "I could not find enough relevant information "
                "in the provided CIS Controls documentation."
            )

        context_parts: list[str] = []

        for index, (
            obj,
            score,
        ) in enumerate(
            ranked_results,
            start=1,
        ):
            properties = obj.properties

            page = properties.get(
                "page_number",
                "Unknown",
            )

            section = (
                properties.get("section_title")
                or "Unknown section"
            )

            content = properties.get(
                "content",
                "",
            )

            context_parts.append(
                (
                    f"SOURCE {index}\n"
                    f"Page: {page}\n"
                    f"Section: {section}\n"
                    f"Relevance score: {score:.4f}\n\n"
                    f"{content}"
                )
            )

        context = (
            "\n\n"
            + ("\n\n" + "-" * 80 + "\n\n").join(
                context_parts
            )
        )

        prompt = f"""
You are a cybersecurity assistant answering questions about
the CIS Critical Security Controls Version 8.

Use only the supplied context.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. If the context does not contain enough information, clearly say so.
4. Answer the user's question directly.
5. Include the relevant page numbers and section names.
6. Do not mention embeddings, retrieval, vector databases, reranking,
   language models, or the internal pipeline.
7. Do not claim that the document requires something unless the context
   explicitly states it.
8. Prefer a concise but complete answer.

QUESTION:
{question}

CONTEXT:
{context}

FINAL ANSWER:
""".strip()

        response = self.model.invoke(prompt)

        content = response.content

        if isinstance(content, str):
            return content.strip()

        return str(content).strip()