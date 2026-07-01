from __future__ import annotations

import json
import os
import time

from dotenv import load_dotenv

from rexa.infra.chat_logging import PipelineRunResult, save_chat_log_best_effort
from rexa.models.answer_v2 import generate_answer_with_metrics
from rexa.models.preprocess import preprocess_with_metrics
from rexa.models.router_v3 import retrieve_with_metrics
from rexa.infra.logger import setup_logger
from rexa.memory import get_history, save_turn

load_dotenv()

log = setup_logger()

_PREPROCESS_HISTORY_MAX_TURNS = int(os.getenv("PREPROCESS_HISTORY_MAX_TURNS", "2"))
_ANSWER_INCLUDE_HISTORY = os.getenv("ANSWER_INCLUDE_HISTORY", "").lower() in {"1", "true", "yes"}


def _tail_history(history: list[dict], max_turns: int) -> list[dict]:
    if max_turns <= 0:
        return []
    return history[-(max_turns * 2):]


def run_query(
    user_input: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> PipelineRunResult:
    started_at = time.perf_counter()
    result = PipelineRunResult(
        user_input=user_input,
        answer="",
        user_id=user_id,
        metadata=dict(metadata or {}),
    )
    log.info(f"[파이프라인] ▶ 시작 | 입력: {user_input!r} | user_id={user_id}")

    try:
        history = get_history(user_id) if user_id else []
        log.info(f"[파이프라인] 메모리 로드: {len(history) // 2}턴")
        log.info(f"[파이프라인] 메모리 : {json.dumps(history, indent=2, ensure_ascii=False)}")

        preprocess_history = _tail_history(history, _PREPROCESS_HISTORY_MAX_TURNS)
        log.info(f"[파이프라인] preprocess 히스토리 사용: {len(preprocess_history) // 2}턴")

        preprocessed, preprocess_metrics = preprocess_with_metrics(user_input, history=preprocess_history)
        result.layer_metrics["preprocess"] = preprocess_metrics
        result.metadata["query_type"] = preprocessed.query_type
        addr_keywords = [a.keyword for a in preprocessed.addresses]
        log.info(f"[파이프라인] preprocess 출력: 주소 {len(addr_keywords)}개 → {addr_keywords}")

        retrieval, router_metrics = retrieve_with_metrics(preprocessed)
        result.layer_metrics["router"] = router_metrics
        result.metadata["retrieval"] = retrieval.get("retrieval", {})
        tool_summary = {k: len(v) for k, v in retrieval.get("retrieval", {}).items()}
        log.info(f"[파이프라인] retrieve 출력: {tool_summary}")

        answer_history = history if _ANSWER_INCLUDE_HISTORY else []
        log.info(f"[파이프라인] answer 히스토리 사용: {len(answer_history) // 2}턴")

        answer, answer_metrics = generate_answer_with_metrics(retrieval, history=answer_history)
        result.layer_metrics["answer"] = answer_metrics
        result.answer = answer
        result.provider = answer_metrics.provider
        result.model_name = answer_metrics.model_name
        log.info(f"[파이프라인] ◀ 완료 | {len(answer)}자")

        if user_id:
            save_turn(user_id, user_input, answer)

        result.status = "success"
        return result
    except Exception as exc:
        result.status = "error"
        result.error_code = type(exc).__name__
        result.error_message = str(exc)
        log.exception(f"[파이프라인] 실패 | input={user_input!r} | {exc}")
        raise
    finally:
        result.total_latency_ms = int((time.perf_counter() - started_at) * 1000)
        result.finalize()
        save_chat_log_best_effort(result)


def run(
    user_input: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> str:
    result = run_query(user_input, user_id=user_id, metadata=metadata)
    answer = result.answer if isinstance(result, PipelineRunResult) else str(result)
    return json.dumps(
        {
            "query": user_input,
            "query_type": result.metadata.get("query_type", ""),
            "answer": answer,
            "retrieval": result.metadata.get("retrieval", {}),
        },
        ensure_ascii=False,
    )
