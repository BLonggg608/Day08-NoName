# RAG Evaluation Results

## Run status

- Framework: RAGAS
- Dataset cases: 15

**Runtime status:** COMPLETED

## A/B retrieval comparison

| Config | Retrieval hit rate |
|---|---:|
| hybrid_rerank | 1.000 |
| hybrid_no_rerank | 1.000 |

Full RAGAS metric scores should be appended from the successful API run.

## QA notes

- Compare only runs using the same golden dataset and source snapshot.
- Keep provider, fallback, and grounding failures separate.
- Do not report a failed provider call as an AI success.
