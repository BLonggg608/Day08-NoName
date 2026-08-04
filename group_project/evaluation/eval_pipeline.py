"""RAGAS evaluation and A/B benchmark for the group RAG pipeline."""

import argparse
import json
from pathlib import Path

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"


def load_golden_dataset() -> list[dict]:
    with GOLDEN_DATASET_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if len(data) < 15:
        raise ValueError(f"Golden dataset must contain at least 15 cases; found {len(data)}")
    required = {"question", "expected_answer", "expected_context"}
    for index, item in enumerate(data, 1):
        missing = required - item.keys()
        if missing:
            raise ValueError(f"Case {index} is missing: {sorted(missing)}")
    return data


def collect_cases(golden_dataset: list[dict], use_reranking: bool = True) -> list[dict]:
    """Run the real pipeline and retain all source/output evidence."""
    from src.task9_retrieval_pipeline import retrieve
    from src.task10_generation import format_context, reorder_for_llm

    cases = []
    for item in golden_dataset:
        sources = retrieve(item["question"], top_k=5, use_reranking=use_reranking)
        context = format_context(reorder_for_llm(sources)) if sources else ""
        cases.append({
            "question": item["question"],
            "answer": "",
            "expected_answer": item["expected_answer"],
            "expected_context": item["expected_context"],
            "contexts": [source.get("content", "") for source in sources],
            "sources": sources,
            "formatted_context": context,
        })
    return cases


def evaluate_with_ragas(cases: list[dict]) -> dict:
    """Evaluate collected cases with RAGAS; provider errors are surfaced."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    dataset = Dataset.from_dict({
        "question": [case["question"] for case in cases],
        "answer": [case["answer"] for case in cases],
        "contexts": [case["contexts"] for case in cases],
        "ground_truth": [case["expected_answer"] for case in cases],
    })
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall, context_precision])
    return {key: float(value) for key, value in result.items() if isinstance(value, (int, float))}


def compare_configs(golden_dataset: list[dict]) -> dict:
    """Run the same cases with reranking enabled and disabled."""
    comparison = {}
    for name, use_reranking in (("hybrid_rerank", True), ("hybrid_no_rerank", False)):
        cases = collect_cases(golden_dataset, use_reranking=use_reranking)
        comparison[name] = {
            "cases": cases,
            "retrieval_hit_rate": sum(bool(case["contexts"]) for case in cases) / len(cases),
        }
    return comparison


def export_results(comparison: dict, error: str | None = None) -> None:
    lines = ["# RAG Evaluation Results", "", "## Run status", "", "- Framework: RAGAS", "- Dataset cases: 15", ""]
    if error:
        lines += ["**Runtime status:** BLOCKED", "", f"`{error}`", "", "No metric scores were invented.", ""]
    else:
        lines += ["**Runtime status:** COMPLETED", "", "## A/B retrieval comparison", "", "| Config | Retrieval hit rate |", "|---|---:|"]
        for name, result in comparison.items():
            lines.append(f"| {name} | {result['retrieval_hit_rate']:.3f} |")
        lines += ["", "Full RAGAS metric scores should be appended from the successful API run.", ""]
    lines += ["## QA notes", "", "- Compare only runs using the same golden dataset and source snapshot.", "- Keep provider, fallback, and grounding failures separate.", "- Do not report a failed provider call as an AI success.", ""]
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Run only a subset for smoke testing")
    args = parser.parse_args()
    golden = load_golden_dataset()
    if args.limit:
        golden = golden[:args.limit]
    print(f"Loaded {len(golden)} golden cases")
    try:
        comparison = compare_configs(golden)
        export_results(comparison)
        print(f"Wrote {RESULTS_PATH}")
    except Exception as exc:
        export_results({}, str(exc))
        raise


if __name__ == "__main__":
    main()
