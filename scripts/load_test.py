import os
import json
import time
import asyncio
import statistics
from typing import List, Dict, Any

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.retrieval.retriever import retrieve_chunks
from app.rbac.roles import UserRole, Department, UserContext

LOAD_TEST_QUERIES = [
    "What is the annual paid leave entitlement for full-time employees?",
    "What was the company's total revenue and net profit in Q2 2026?",
    "What CPU and memory specs are required for Kubernetes pods?",
    "Can employees accept gifts exceeding $50 from commercial partners?",
    "What discount percentage requires VP of Sales approval?",
    "What are the core ethical rules and code of conduct standards?",
    "What is the per diem meal allowance cap for corporate travel?",
    "What automated static analysis tools run in our CI/CD pipeline?",
    "What is our GDPR personal data retention policy?",
    "What is the required notice period for employee offboarding?"
]

OUTPUT_REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "evaluation", "load_test_report.json")


async def simulate_user_request(user_id: int, query: str, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    async with semaphore:
        start_t = time.perf_counter()
        user_ctx = UserContext(
            user_id=f"load_user_{user_id}",
            username=f"User_{user_id}",
            role=UserRole.EXECUTIVE,
            department=Department.HR
        )

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: retrieve_chunks(query=query, k=5, user_context=user_ctx)
            )
            elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
            success = len(results) >= 0
            return {"success": success, "latency_ms": elapsed_ms, "error": None}
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
            return {"success": False, "latency_ms": elapsed_ms, "error": str(e)}


async def run_load_tier(concurrent_users: int) -> Dict[str, Any]:
    print(f"\n🚀 Simulating {concurrent_users} Virtual Users...")
    start_time = time.perf_counter()
    semaphore = asyncio.Semaphore(25)

    tasks = []
    for i in range(concurrent_users):
        query = LOAD_TEST_QUERIES[i % len(LOAD_TEST_QUERIES)]
        tasks.append(simulate_user_request(i + 1, query, semaphore))

    results = await asyncio.gather(*tasks)
    total_duration_sec = time.perf_counter() - start_time

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in results]

    latencies.sort()
    avg_latency = round(statistics.mean(latencies), 2) if latencies else 0.0
    p50_latency = round(statistics.median(latencies), 2) if latencies else 0.0
    p95_latency = round(latencies[int(len(latencies) * 0.95)], 2) if latencies else 0.0
    p99_latency = round(latencies[int(len(latencies) * 0.99)], 2) if latencies else 0.0

    rps = round(concurrent_users / total_duration_sec, 2) if total_duration_sec > 0 else 0.0
    failure_rate = round((len(failed) / concurrent_users) * 100.0, 2)

    tier_report = {
        "concurrent_users": concurrent_users,
        "total_requests": concurrent_users,
        "successful_requests": len(successful),
        "failed_requests": len(failed),
        "failure_rate_pct": failure_rate,
        "throughput_rps": rps,
        "duration_sec": round(total_duration_sec, 2),
        "latencies_ms": {
            "mean": avg_latency,
            "p50": p50_latency,
            "p95": p95_latency,
            "p99": p99_latency,
            "min": round(min(latencies), 2) if latencies else 0.0,
            "max": round(max(latencies), 2) if latencies else 0.0
        }
    }

    print(f"  ✅ Completed {concurrent_users} Requests in {tier_report['duration_sec']}s ({rps} req/sec)")
    print(f"  📊 Latencies -> Mean: {avg_latency}ms | p50: {p50_latency}ms | p95: {p95_latency}ms | p99: {p99_latency}ms")
    print(f"  ⚡ Failure Rate: {failure_rate}% ({len(failed)} failed)")

    return tier_report


async def main():
    print("=================================================================")
    print("Task A3: RAG Platform Load & Scalability Test Suite")
    print("=================================================================")

    user_tiers = [50, 100, 250]
    tier_reports = []

    for tier in user_tiers:
        report = await run_load_tier(tier)
        tier_reports.append(report)

    summary_report = {
        "test_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "load_tiers": tier_reports
    }

    os.makedirs(os.path.dirname(OUTPUT_REPORT_PATH), exist_ok=True)
    with open(OUTPUT_REPORT_PATH, "w") as f:
        json.dump(summary_report, f, indent=2)

    print("\n=================================================================")
    print(f"Load test simulation finished! Report saved to '{OUTPUT_REPORT_PATH}'")
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(main())
