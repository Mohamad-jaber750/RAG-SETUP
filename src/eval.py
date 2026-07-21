from __future__ import annotations
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"

DATASET_PATH = EVALUATION_DIR / "golden_dataset.json"
OUTPUTS_PATH = EVALUATION_DIR / "rag_outputs.json"
SUMMARY_PATH = EVALUATION_DIR / "evaluation_summary.json"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ============================================================
# CONFIGURATION
# ============================================================

JUDGE_MODEL = os.getenv("DEEPEVAL_JUDGE_MODEL", "gemma3:4b")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434"),
)

METRIC_THRESHOLD = float(os.getenv("DEEPEVAL_THRESHOLD", "0.5"))

# Set to 0 to evaluate the complete dataset.
MAX_CASES = int(os.getenv("EVAL_MAX_CASES", "0"))

# Set to 1 to regenerate answers even when checkpointed answers exist.
FORCE_REGENERATE = os.getenv("EVAL_FORCE_REGENERATE", "0") == "1"

# DeepEval can be slow with a local judge model.
# Synchronous execution is safer for Ollama and small local models.
RUN_ASYNC = os.getenv("DEEPEVAL_ASYNC", "0") == "1"


# ============================================================
# DATASET
# ============================================================

def load_dataset(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{path}\n\n"
            "Create evaluation/golden_dataset.json first."
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            dataset = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path}\n"
            f"Line: {error.lineno}, column: {error.colno}\n"
            f"Problem: {error.msg}"
        ) from error

    if not isinstance(dataset, list):
        raise ValueError(
            "The dataset must be one JSON array containing question objects."
        )

    if not dataset:
        raise ValueError("The evaluation dataset is empty.")

    validate_dataset(dataset)

    if MAX_CASES > 0:
        dataset = dataset[:MAX_CASES]

    return dataset


def validate_dataset(dataset: list[dict[str, Any]]) -> None:
    required_fields = {
        "input",
        "expected_output",
        "context",
    }

    for index, item in enumerate(dataset, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Dataset item {index} must be a JSON object."
            )

        missing = required_fields - item.keys()

        if missing:
            raise ValueError(
                f"Dataset item {index} is missing fields: "
                f"{', '.join(sorted(missing))}"
            )

        if not isinstance(item["input"], str) or not item["input"].strip():
            raise ValueError(
                f"Dataset item {index} has an invalid 'input' value."
            )

        if (
            not isinstance(item["expected_output"], str)
            or not item["expected_output"].strip()
        ):
            raise ValueError(
                f"Dataset item {index} has an invalid "
                "'expected_output' value."
            )

        if not isinstance(item["context"], list):
            raise ValueError(
                f"Dataset item {index}: 'context' must be a list of strings."
            )

        if not all(isinstance(value, str) for value in item["context"]):
            raise ValueError(
                f"Dataset item {index}: every context entry must be a string."
            )


# ============================================================
# PIPELINE IMPORT
# ============================================================

def create_pipeline() -> Any:
    """
    Imports and initializes the RAG pipeline.

    This supports several common pipeline.py styles:

    1. create_pipeline()
    2. RAGPipeline()
    3. Pipeline()
    4. module-level answer(question)
    """

    try:
        import pipeline as pipeline_module
    except ImportError as error:
        raise ImportError(
            "Could not import src/pipeline.py.\n"
            "Make sure the file exists and your imports inside it are valid."
        ) from error

    if hasattr(pipeline_module, "create_pipeline"):
        print("Initializing pipeline with create_pipeline()...")
        return pipeline_module.create_pipeline()

    if hasattr(pipeline_module, "RAGPipeline"):
        print("Initializing RAGPipeline...")
        return pipeline_module.RAGPipeline()

    if hasattr(pipeline_module, "Pipeline"):
        print("Initializing Pipeline...")
        return pipeline_module.Pipeline()

    if hasattr(pipeline_module, "answer"):
        print("Using module-level pipeline.answer()...")
        return pipeline_module

    raise AttributeError(
        "Could not find a supported pipeline entry point.\n\n"
        "Your src/pipeline.py must expose one of:\n"
        "  create_pipeline()\n"
        "  RAGPipeline\n"
        "  Pipeline\n"
        "  answer(question)"
    )


# ============================================================
# PIPELINE RESULT NORMALIZATION
# ============================================================

def run_pipeline(pipeline: Any, question: str) -> dict[str, Any]:
    """
    Calls the pipeline and normalizes its output.

    Supported pipeline methods:
      pipeline.answer(question)
      pipeline.query(question)
      pipeline.run(question)
      pipeline.ask(question)

    Supported returned values:
      - plain string
      - tuple: (answer, contexts)
      - dictionary
      - object with answer/context attributes
    """

    method = None

    for method_name in ("answer", "query", "run", "ask"):
        candidate = getattr(pipeline, method_name, None)

        if callable(candidate):
            method = candidate
            break

    if method is None:
        raise AttributeError(
            "The pipeline has no callable answer(), query(), run(), or ask() "
            "method."
        )

    raw_result = method(question)

    actual_output, retrieval_context, source_metadata = normalize_pipeline_result(
        raw_result
    )

    if not actual_output.strip():
        raise ValueError("The pipeline returned an empty answer.")

    return {
        "actual_output": actual_output,
        "retrieval_context": retrieval_context,
        "source_metadata": source_metadata,
    }


def normalize_pipeline_result(
    result: Any,
) -> tuple[str, list[str], list[dict[str, Any]]]:
    if isinstance(result, str):
        return result, [], []

    if isinstance(result, tuple):
        if len(result) < 2:
            return str(result[0]), [], []

        answer = str(result[0])
        contexts, metadata = normalize_contexts(result[1])

        return answer, contexts, metadata

    if isinstance(result, dict):
        answer = first_available(
            result,
            [
                "answer",
                "actual_output",
                "response",
                "generated_answer",
                "output",
                "text",
                "result",
            ],
        )

        context_value = first_available(
    result,
    [
        "reranked_sources",      # <- use these first
        "retrieved_sources",
        "retrieval_context",
        "retrieved_context",
        "contexts",
        "context",
        "retrieved_chunks",
        "chunks",
        "documents",
        "sources",
    ],
    default=[],
)

        contexts, metadata = normalize_contexts(context_value)

        return str(answer or ""), contexts, metadata

    answer = first_attribute(
        result,
        [
            "answer",
            "actual_output",
            "response",
            "generated_answer",
            "output",
            "text",
        ],
    )

    context_value = first_attribute(
        result,
        [
            "retrieval_context",
            "retrieved_context",
            "contexts",
            "context",
            "retrieved_chunks",
            "chunks",
            "documents",
            "sources",
        ],
        default=[],
    )

    contexts, metadata = normalize_contexts(context_value)

    return str(answer or result), contexts, metadata


def normalize_contexts(
    context_value: Any,
) -> tuple[list[str], list[dict[str, Any]]]:
    if context_value is None:
        return [], []

    if isinstance(context_value, str):
        return [context_value], []

    if isinstance(context_value, dict):
        context_value = [context_value]

    if not isinstance(context_value, (list, tuple)):
        return [str(context_value)], []

    contexts: list[str] = []
    metadata_list: list[dict[str, Any]] = []

    for item in context_value:
        text, metadata = normalize_single_context(item)

        if text.strip():
            contexts.append(text.strip())
            metadata_list.append(metadata)

    return contexts, metadata_list


def normalize_single_context(
    item: Any,
) -> tuple[str, dict[str, Any]]:
    if isinstance(item, str):
        return item, {}

    if isinstance(item, dict):
        text = first_available(
            item,
            [
                "text",
                "content",
                "chunk",
                "page_content",
                "document",
                "body",
                "context",
            ],
            default="",
        )

        metadata = item.get("metadata", {})

        if not isinstance(metadata, dict):
            metadata = {"metadata": metadata}

        for key in (
            "page",
            "page_number",
            "section",
            "safeguard",
            "source",
            "title",
            "score",
            "rerank_score",
            "distance",
        ):
            if key in item and key not in metadata:
                metadata[key] = item[key]

        return str(text), metadata

    text = first_attribute(
        item,
        [
            "text",
            "content",
            "chunk",
            "page_content",
            "document",
            "body",
            "context",
        ],
        default=str(item),
    )

    metadata = getattr(item, "metadata", {})

    if not isinstance(metadata, dict):
        metadata = {"metadata": str(metadata)}

    return str(text), metadata


def first_available(
    data: dict[str, Any],
    keys: list[str],
    default: Any = None,
) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]

    return default


def first_attribute(
    obj: Any,
    attributes: list[str],
    default: Any = None,
) -> Any:
    for attribute in attributes:
        if hasattr(obj, attribute):
            value = getattr(obj, attribute)

            if value is not None:
                return value

    return default


# ============================================================
# CHECKPOINTS
# ============================================================

def load_existing_outputs() -> dict[str, dict[str, Any]]:
    if not OUTPUTS_PATH.exists():
        return {}

    try:
        with OUTPUTS_PATH.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except (json.JSONDecodeError, OSError):
        print(
            "Warning: existing rag_outputs.json could not be read. "
            "Starting a new checkpoint."
        )
        return {}

    if not isinstance(records, list):
        return {}

    indexed: dict[str, dict[str, Any]] = {}

    for record in records:
        if not isinstance(record, dict):
            continue

        case_id = str(record.get("id", "")).strip()

        if case_id:
            indexed[case_id] = record

    return indexed


def save_outputs(records: list[dict[str, Any]]) -> None:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# TEST CASE CREATION
# ============================================================

def build_test_cases(
    pipeline: Any,
    dataset: list[dict[str, Any]],
) -> tuple[list[LLMTestCase], list[dict[str, Any]]]:
    existing_outputs = load_existing_outputs()

    test_cases: list[LLMTestCase] = []
    output_records: list[dict[str, Any]] = []

    total = len(dataset)

    for index, item in enumerate(dataset, start=1):
        question = item["input"].strip()
        expected_output = item["expected_output"].strip()
        reference_context = [
            value.strip()
            for value in item.get("context", [])
            if value.strip()
        ]

        additional_metadata = item.get("additional_metadata", {})

        if not isinstance(additional_metadata, dict):
            additional_metadata = {}

        case_id = str(
            additional_metadata.get("id", f"G{index:02d}")
        )

        case_name = str(
            item.get("name", case_id)
        )

        print("\n" + "=" * 70)
        print(f"[{index}/{total}] {case_id} - {case_name}")
        print("=" * 70)
        print(f"Question: {question}")

        checkpoint = existing_outputs.get(case_id)

        if checkpoint and not FORCE_REGENERATE:
            print("Using checkpointed RAG output.")

            actual_output = str(
                checkpoint.get("actual_output", "")
            )

            retrieval_context = checkpoint.get(
                "retrieval_context",
                [],
            )

            source_metadata = checkpoint.get(
                "source_metadata",
                [],
            )
        else:
            print("Running RAG pipeline...")

            pipeline_result = run_pipeline(
                pipeline=pipeline,
                question=question,
            )

            actual_output = pipeline_result["actual_output"]
            retrieval_context = pipeline_result["retrieval_context"]
            source_metadata = pipeline_result["source_metadata"]

        if not isinstance(retrieval_context, list):
            retrieval_context = [str(retrieval_context)]

        retrieval_context = [
            str(value).strip()
            for value in retrieval_context
            if str(value).strip()
        ]

        print(f"Answer: {actual_output}")
        print(f"Retrieved chunks: {len(retrieval_context)}")

        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
            expected_output=expected_output,
            context=reference_context,
            retrieval_context=retrieval_context,
        )

        test_cases.append(test_case)

        output_record = {
            "id": case_id,
            "name": case_name,
            "input": question,
            "expected_output": expected_output,
            "actual_output": actual_output,
            "context": reference_context,
            "retrieval_context": retrieval_context,
            "source_metadata": source_metadata,
            "additional_metadata": additional_metadata,
            "generated_at": datetime.now().isoformat(),
        }

        output_records.append(output_record)

        # Save after every case so progress is not lost.
        save_outputs(output_records)

    return test_cases, output_records


# ============================================================
# DEEPEVAL METRICS
# ============================================================

def create_judge_model() -> OllamaModel:
    print("\nInitializing DeepEval judge...")
    print(f"Judge model: {JUDGE_MODEL}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")

    return OllamaModel(
        model=JUDGE_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )


def create_metrics(judge: OllamaModel) -> list[Any]:
    return [
        FaithfulnessMetric(
            threshold=METRIC_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=RUN_ASYNC,
        ),
        AnswerRelevancyMetric(
            threshold=METRIC_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=RUN_ASYNC,
        ),
        ContextualRelevancyMetric(
            threshold=METRIC_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=RUN_ASYNC,
        ),
        ContextualPrecisionMetric(
            threshold=METRIC_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=RUN_ASYNC,
        ),
        ContextualRecallMetric(
            threshold=METRIC_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=RUN_ASYNC,
        ),
    ]


# ============================================================
# SUMMARY
# ============================================================

def extract_evaluation_summary(result: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "judge_model": JUDGE_MODEL,
        "ollama_base_url": OLLAMA_BASE_URL,
        "threshold": METRIC_THRESHOLD,
        "created_at": datetime.now().isoformat(),
        "raw_result_type": type(result).__name__,
    }

    test_results = getattr(result, "test_results", None)

    if test_results is None and isinstance(result, list):
        test_results = result

    if not test_results:
        summary["message"] = (
            "DeepEval completed, but no structured test_results "
            "were available for local summary extraction."
        )
        return summary

    cases: list[dict[str, Any]] = []

    for index, test_result in enumerate(test_results, start=1):
        case_summary: dict[str, Any] = {
            "index": index,
            "input": getattr(test_result, "input", None),
            "success": getattr(test_result, "success", None),
            "metrics": [],
        }

        metrics_data = getattr(
            test_result,
            "metrics_data",
            [],
        ) or []

        for metric_data in metrics_data:
            case_summary["metrics"].append(
                {
                    "name": getattr(
                        metric_data,
                        "name",
                        type(metric_data).__name__,
                    ),
                    "score": getattr(metric_data, "score", None),
                    "threshold": getattr(
                        metric_data,
                        "threshold",
                        None,
                    ),
                    "success": getattr(
                        metric_data,
                        "success",
                        None,
                    ),
                    "reason": getattr(
                        metric_data,
                        "reason",
                        None,
                    ),
                    "error": getattr(
                        metric_data,
                        "error",
                        None,
                    ),
                }
            )

        cases.append(case_summary)

    summary["cases"] = cases
    summary["number_of_cases"] = len(cases)

    return summary


def save_summary(summary: dict[str, Any]) -> None:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    with SUMMARY_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# CLEANUP
# ============================================================

def close_pipeline(pipeline: Any) -> None:
    if pipeline is None:
        return

    for method_name in (
        "close",
        "shutdown",
        "disconnect",
        "cleanup",
    ):
        method = getattr(pipeline, method_name, None)

        if callable(method):
            try:
                method()
            except Exception as error:
                print(
                    f"Warning: pipeline cleanup failed through "
                    f"{method_name}(): {error}"
                )

            return

    # Some pipeline classes store the Weaviate client as an attribute.
    for attribute_name in (
        "client",
        "weaviate_client",
        "vector_client",
    ):
        client = getattr(pipeline, attribute_name, None)

        close_method = getattr(client, "close", None)

        if callable(close_method):
            try:
                close_method()
            except Exception as error:
                print(
                    f"Warning: Weaviate client cleanup failed: {error}"
                )

            return


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    pipeline = None

    try:
        print("=" * 70)
        print("CIS CONTROLS RAG EVALUATION WITH DEEPEVAL")
        print("=" * 70)

        print(f"\nDataset: {DATASET_PATH}")
        dataset = load_dataset()

        print(f"Loaded {len(dataset)} evaluation cases.")

        if MAX_CASES > 0:
            print(f"Evaluation limited to {MAX_CASES} cases.")

        pipeline = create_pipeline()

        print("\nRAG pipeline ready.")

        test_cases, output_records = build_test_cases(
            pipeline=pipeline,
            dataset=dataset,
        )

        print(
            f"\nGenerated {len(output_records)} RAG outputs."
        )
        print(f"Checkpoint saved to: {OUTPUTS_PATH}")

        judge = create_judge_model()
        metrics = create_metrics(judge)

        print("\nStarting DeepEval...")
        print(
            "Metrics: Faithfulness, Answer Relevancy, "
            "Contextual Relevancy, Contextual Precision, "
            "Contextual Recall"
        )
        print(
            "This may take a long time because every metric uses "
            "the local judge model."
        )

        result = evaluate(
    test_cases=test_cases,
    metrics=metrics,
    async_config=AsyncConfig(
        run_async=False,
    ),
)

        summary = extract_evaluation_summary(result)
        save_summary(summary)

        print("\nEvaluation complete.")
        print(f"Summary saved to: {SUMMARY_PATH}")

    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user.")

    except Exception as error:
        print("\nEvaluation failed.")
        print(f"{type(error).__name__}: {error}")
        print("\nFull traceback:")
        traceback.print_exc()

        raise

    finally:
        close_pipeline(pipeline)
        print("\nPipeline connection closed.")


if __name__ == "__main__":
    main()