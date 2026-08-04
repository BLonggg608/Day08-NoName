# RAG Evaluation Results

## Framework sử dụng

> RAGAS với OpenRouter làm LLM judge. Golden dataset gồm 15 câu hỏi.

**Runtime status:** COMPLETED cho cả Config A và Config B.

---

## Overall Scores

| Metric | Config A: Hybrid + Rerank | Config B: Hybrid without Rerank |
|---|---:|---:|
| Faithfulness | 0.7690 | 0.7349 |
| Answer Relevance | 0.4399 | 0.4736 |
| Context Recall | 0.9333 | 0.9333 |
| Context Precision | 0.7881 | 0.8094 |
| **Average** | **0.7326** | **0.7378** |

---

## A/B Comparison Analysis

- Config A có Faithfulness cao hơn: `0.7690` so với `0.7349`.
- Config B có Answer Relevance cao hơn: `0.4736` so với `0.4399`.
- Context Recall bằng nhau: `0.9333`.
- Config B có Context Precision cao hơn: `0.8094` so với `0.7881`.
- Config B có Average cao hơn nhẹ: `0.7378` so với `0.7326`.

**Kết luận:** Trong lần chạy mới nhất, Config B — Hybrid Search without Rerank — đạt điểm trung bình cao hơn nhẹ. Config A vẫn tốt hơn về Faithfulness. Chênh lệch nhỏ nên cần giữ nguyên dataset, source snapshot và model judge khi so sánh các lần chạy sau.

---

## Worst Performers (Config A)

Xếp hạng theo trung bình các metric per-case hợp lệ. Giá trị `NaN` không được thay bằng 0 và không được dùng để tính average.

| # | Question | Faithfulness | Relevance | Recall | Precision | Average |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Có thể yêu cầu bản PDF của điều khoản học bổng bằng cách nào? | 0.0000 | 0.0000 | 0.0000 | 0.3333 | 0.0833 |
| 2 | Một học bổng có thể có điều khoản riêng bổ sung không? | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 0.5000 |
| 3 | Brochure có đề cập đến tài chính không? | 0.8000 | 0.0000 | 1.0000 | 0.7000 | 0.6250 |

### Missing per-case metric

Một case có Faithfulness là `NaN` do judge trả output không parse được. Đây là lỗi đo lường, không phải điểm 0.

---

## Root Cause Analysis

1. Câu hỏi về bản PDF học bổng có context recall bằng 0, cho thấy retriever chưa lấy được evidence email liên quan.
2. Câu hỏi về điều khoản học bổng có context nhưng answer không đạt Faithfulness/Relevance.
3. Câu hỏi về brochure có Context Recall tốt nhưng Answer Relevance bằng 0; câu trả lời chưa trả lời trực tiếp câu hỏi.
4. Một per-case Faithfulness bị `NaN` vì judge trả output không parse được.

---

## Recommendations

1. Bổ sung hoặc làm rõ chunk chứa email yêu cầu bản PDF điều khoản học bổng.
2. Yêu cầu generator trả lời đúng facts được hỏi trước, sau đó mới thêm giải thích và citation.
3. Validate mỗi citation phải trỏ tới source có trong retrieved context.
4. Retry riêng metric bị `NaN`; không thay `NaN` bằng 0.
