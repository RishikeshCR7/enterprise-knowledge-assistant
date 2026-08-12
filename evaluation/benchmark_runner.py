import os
import json
import time
import logging
from typing import List, Dict, Any

from app.agents.rag_graph import rag_graph
from app.rbac.roles import UserRole, Department, UserContext
from app.database.eval_db import eval_db
from app.utils.observability import TelemetryTracker

logger = logging.getLogger(__name__)

BENCHMARK_PATH = os.path.join(os.path.dirname(__file__), "benchmark.json")
OUTPUT_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "benchmark_results.json")


def compute_metrics(
    retrieved_chunks: List[Dict[str, Any]],
    expected_doc_id: str,
    generated_text: str,
    expected_keywords: List[str]
) -> Dict[str, float]:
    """
    Computes Context Precision, Context Recall, Faithfulness, Answer Relevancy, and Hallucination Rate.
    """
    # 1. Context Precision & Recall
    if not expected_doc_id:
        # Refusal test case
        precision = 1.0 if not retrieved_chunks else 0.0
        recall = 1.0 if not retrieved_chunks else 0.0
    else:
        retrieved_ids = [c.get("metadata", {}).get("doc_id") for c in retrieved_chunks]
        hit = 1 if expected_doc_id in retrieved_ids else 0
        precision = hit / len(retrieved_chunks) if retrieved_chunks else 0.0
        recall = float(hit)

    # 2. Faithfulness & Hallucination Rate
    gen_lower = generated_text.lower()
    matched_kws = sum(1 for kw in expected_keywords if kw.lower() in gen_lower)
    faithfulness = matched_kws / len(expected_keywords) if expected_keywords else 1.0
    hallucination_rate = round(1.0 - faithfulness, 4)

    # 3. Answer Relevancy
    relevancy = round((precision * 0.4) + (faithfulness * 0.6), 4)

    return {
        "context_precision": round(precision, 4),
        "context_recall": round(recall, 4),
        "faithfulness": round(faithfulness, 4),
        "answer_relevancy": round(relevancy, 4),
        "hallucination_rate": hallucination_rate
    }


def run_benchmark():
    """
    Task A1: Executes 50-Question Enterprise RAG Benchmark Suite.
    """
    if not os.path.exists(BENCHMARK_PATH):
        logger.error(f"Benchmark file not found at {BENCHMARK_PATH}")
        return

    with open(BENCHMARK_PATH, "r") as f:
        benchmark_data = json.load(f)

    logger.info(f"Running 50-Question Enterprise RAG Benchmark Suite across {len(benchmark_data)} queries...")
    results = []

    user_ctx = UserContext(
        user_id="bench_eval_user",
        username="BenchmarkEvaluator",
        role=UserRole.EXECUTIVE,
        department=Department.HR
    )

    total_precision = 0.0
    total_recall = 0.0
    total_faithfulness = 0.0
    total_relevancy = 0.0
    total_hallucination = 0.0
    total_latency_ms = 0.0

    for idx, item in enumerate(benchmark_data, 1):
        query = item["query"]
        category = item.get("category", "General")
        expected_doc_id = item.get("expected_doc_id")
        expected_keywords = item.get("expected_keywords", [])

        tracker = TelemetryTracker()
        start_t = time.perf_counter()

        output = rag_graph.invoke({
            "question": query,
            "user_context": user_ctx.model_dump()
        })

        elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
        total_latency_ms += elapsed_ms

        retrieved_docs = output.get("retrieved_docs", []) or []
        generated_text = output.get("generation", "") or ""
        confidence_score = output.get("confidence_score", 0)

        tracker.estimate_tokens_and_cost(query, generated_text)
        tracker.finish_and_save()

        metrics = compute_metrics(retrieved_docs, expected_doc_id, generated_text, expected_keywords)

        total_precision += metrics["context_precision"]
        total_recall += metrics["context_recall"]
        total_faithfulness += metrics["faithfulness"]
        total_relevancy += metrics["answer_relevancy"]
        total_hallucination += metrics["hallucination_rate"]

        eval_db.insert_evaluation(
            query=query,
            answer=generated_text[:200],
            faithfulness=metrics["faithfulness"],
            answer_relevancy=metrics["answer_relevancy"],
            context_precision=metrics["context_precision"],
            context_recall=metrics["context_recall"],
            hallucination_rate=metrics["hallucination_rate"],
            latency_ms=elapsed_ms
        )

        res_item = {
            "id": item["id"],
            "query": query,
            "category": category,
            "expected_doc_id": expected_doc_id,
            "confidence_score": confidence_score,
            "latency_ms": elapsed_ms,
            "metrics": metrics
        }
        results.append(res_item)
        print(f"[{item['id']}] [{category}] '{query[:35]}...' -> Confidence: {confidence_score}% | Latency: {elapsed_ms}ms | Relevancy: {metrics['answer_relevancy']}")

    count = len(benchmark_data)
    summary = {
        "total_queries": count,
        "mean_context_precision": round(total_precision / count, 4),
        "mean_context_recall": round(total_recall / count, 4),
        "mean_faithfulness": round(total_faithfulness / count, 4),
        "mean_answer_relevancy": round(total_relevancy / count, 4),
        "mean_hallucination_rate": round(total_hallucination / count, 4),
        "mean_latency_ms": round(total_latency_ms / count, 2),
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    report = {
        "summary": summary,
        "detailed_results": results
    }

    with open(OUTPUT_RESULTS_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=================================================================")
    print("50-QUESTION ENTERPRISE BENCHMARK RESULTS SUMMARY:")
    print(f"  - Mean Context Precision  : {summary['mean_context_precision']}")
    print(f"  - Mean Context Recall     : {summary['mean_context_recall']}")
    print(f"  - Mean Faithfulness       : {summary['mean_faithfulness']}")
    print(f"  - Mean Answer Relevancy   : {summary['mean_answer_relevancy']}")
    print(f"  - Mean Hallucination Rate : {summary['mean_hallucination_rate']}")
    print(f"  - Mean Latency            : {summary['mean_latency_ms']} ms")
    print("=================================================================")
    print(f"Report saved to '{OUTPUT_RESULTS_PATH}' and SQLite database.")


if __name__ == "__main__":
    run_benchmark()
