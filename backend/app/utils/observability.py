import time
import uuid
import logging
from typing import Dict, Any, Optional
from app.database.eval_db import eval_db

logger = logging.getLogger(__name__)

# Token cost estimation ($0.0001 per 1k prompt tokens, $0.0002 per 1k completion tokens)
PROMPT_COST_PER_1K = 0.0001
COMPLETION_COST_PER_1K = 0.0002


class TelemetryTracker:
    """
    Task A3: Telemetry & Observability Tracker measuring execution latencies and token/cost metrics.
    """
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.start_time = time.perf_counter()
        self.timings: Dict[str, float] = {
            "retrieval_ms": 0.0,
            "embedding_ms": 0.0,
            "reranker_ms": 0.0,
            "llm_ms": 0.0,
        }
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.cost_usd = 0.0
        self.cache_hit = False

    def record_stage(self, stage_name: str, duration_ms: float):
        if stage_name in self.timings:
            self.timings[stage_name] = round(duration_ms, 2)

    def estimate_tokens_and_cost(self, prompt_text: str, completion_text: str):
        # Approximate 1 token = ~4 characters
        self.prompt_tokens = max(1, len(prompt_text) // 4)
        self.completion_tokens = max(1, len(completion_text) // 4)
        self.total_tokens = self.prompt_tokens + self.completion_tokens

        prompt_cost = (self.prompt_tokens / 1000.0) * PROMPT_COST_PER_1K
        completion_cost = (self.completion_tokens / 1000.0) * COMPLETION_COST_PER_1K
        self.cost_usd = round(prompt_cost + completion_cost, 6)

    def finish_and_save(self) -> Dict[str, Any]:
        total_ms = round((time.perf_counter() - self.start_time) * 1000.0, 2)
        
        telemetry_data = {
            "trace_id": self.trace_id,
            "retrieval_ms": self.timings.get("retrieval_ms", 0.0),
            "embedding_ms": self.timings.get("embedding_ms", 0.0),
            "reranker_ms": self.timings.get("reranker_ms", 0.0),
            "llm_ms": self.timings.get("llm_ms", 0.0),
            "total_ms": total_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "cache_hit": self.cache_hit
        }

        try:
            eval_db.insert_telemetry(
                trace_id=self.trace_id,
                retrieval_ms=telemetry_data["retrieval_ms"],
                embedding_ms=telemetry_data["embedding_ms"],
                reranker_ms=telemetry_data["reranker_ms"],
                llm_ms=telemetry_data["llm_ms"],
                total_ms=total_ms,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                total_tokens=self.total_tokens,
                cost_usd=self.cost_usd,
                cache_hit=self.cache_hit
            )
        except Exception as e:
            logger.error(f"Error persisting telemetry trace {self.trace_id}: {str(e)}")

        return telemetry_data
