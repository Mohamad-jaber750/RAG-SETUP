from __future__ import annotations

import json
import re
from typing import Any

from langchain_ollama import ChatOllama


JUDGE_MODEL = "gemma3:4b"


class GemmaJudge:
    def __init__(
        self,
        base_url: str,
    ) -> None:
        print(
            f"Initializing judge: "
            f"{JUDGE_MODEL}"
        )

        self.model = ChatOllama(
            model=JUDGE_MODEL,
            base_url=base_url,
            temperature=0,
            format="json",
            num_ctx=4096,
        )

        print("Gemma judge ready")

    def judge(
        self,
        question: str,
        gold_answer: str | None,
        generated_answer: str,
        retrieved_context: str,
        answerable: bool,
    ) -> dict[str, Any]:
        gold_text = (
            gold_answer
            if gold_answer is not None
            else (
                "The supplied CIS Controls documentation "
                "does not provide a supported answer."
            )
        )

        prompt = f"""
You are an impartial evaluator for a cybersecurity RAG system.

Evaluate the generated answer using the question, gold answer,
and retrieved context.

QUESTION:
{question}

IS THE QUESTION ANSWERABLE FROM THE DOCUMENT?
{answerable}

GOLD ANSWER:
{gold_text}

RETRIEVED CONTEXT:
{retrieved_context}

GENERATED ANSWER:
{generated_answer}

Evaluation dimensions:

1. correctness:
   Does the generated answer agree with the gold answer?

2. completeness:
   Does it include the important information from the gold answer?

3. relevance:
   Does it directly answer the question without unnecessary information?

4. faithfulness:
   Are its factual claims supported by the retrieved context?

5. hallucination:
   True when the answer contains unsupported or invented factual claims.

6. refusal_correct:
   For an unanswerable question, true only when the generated answer
   correctly says the documentation does not contain enough information.
   For answerable questions, this should normally be false.

7. overall:
   A balanced overall quality score.

Scoring:
- correctness: integer from 0 to 10
- completeness: integer from 0 to 10
- relevance: integer from 0 to 10
- faithfulness: integer from 0 to 10
- overall: integer from 0 to 10
- hallucination: boolean
- refusal_correct: boolean
- reason: brief explanation

Rules:
- Compare meaning, not exact wording.
- Do not require the generated answer to copy the gold answer.
- Penalize important missing details.
- Penalize unsupported claims.
- Do not claim that a citation exists unless the generated answer
  actually contains a page number or section reference.
- Return only valid JSON.

Return exactly this structure:

{{
  "correctness": 0,
  "completeness": 0,
  "relevance": 0,
  "faithfulness": 0,
  "hallucination": false,
  "refusal_correct": false,
  "overall": 0,
  "reason": "brief explanation"
}}
""".strip()

        response = self.model.invoke(prompt)

        return self._parse_json_response(
            response.content
        )

    @staticmethod
    def _parse_json_response(
        content: Any,
    ) -> dict[str, Any]:
        text = (
            content
            if isinstance(content, str)
            else str(content)
        ).strip()

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            # Fallback if the model wraps JSON in a code block.
            match = re.search(
                r"\{.*\}",
                text,
                re.DOTALL,
            )

            if match is None:
                raise RuntimeError(
                    "Judge returned invalid JSON:\n"
                    f"{text}"
                )

            try:
                return json.loads(
                    match.group(0)
                )

            except json.JSONDecodeError as error:
                raise RuntimeError(
                    "Judge returned invalid JSON:\n"
                    f"{text}"
                ) from error