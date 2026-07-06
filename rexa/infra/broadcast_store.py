from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID
import logging
import os

from rexa.infra.chat_logging import (
    CHAT_USERS_TABLE,
    _sql_literal,
    decrypt_user_id,
    ensure_chat_users_table,
    run_sql,
    sql_quote,
)

log = logging.getLogger("rexa")

BROADCAST_SEND_LOG_TABLE = os.getenv("BROADCAST_SEND_LOG_TABLE", "broadcast_send_logs").strip() or "broadcast_send_logs"

_BROADCAST_TABLES_READY = False


@dataclass
class BroadcastTarget:
    user_key: str
    user_id: str
    last_seen_at: str | None = None


@dataclass
class SendLogRow:
    user_key: str
    status: str  # SENT / FAILED / SKIPPED / DRY_RUN
    http_status: int | None = None
    task_id: str | None = None
    error_message: str | None = None


def ensure_broadcast_tables() -> None:
    global _BROADCAST_TABLES_READY
    if _BROADCAST_TABLES_READY:
        return

    ensure_chat_users_table()
    run_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {BROADCAST_SEND_LOG_TABLE} (
            id BIGSERIAL PRIMARY KEY,
            batch_id UUID NOT NULL,
            run_date DATE NOT NULL,
            event_name VARCHAR(100) NOT NULL,
            user_key VARCHAR(128) NOT NULL,
            chunk_index INTEGER NOT NULL,
            http_status INTEGER,
            task_id VARCHAR(100),
            status VARCHAR(20) NOT NULL,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_{BROADCAST_SEND_LOG_TABLE}_sent_once
            ON {BROADCAST_SEND_LOG_TABLE} (run_date, event_name, user_key) WHERE status = 'SENT';
        CREATE INDEX IF NOT EXISTS idx_{BROADCAST_SEND_LOG_TABLE}_batch
            ON {BROADCAST_SEND_LOG_TABLE} (batch_id);
        """
    )
    _BROADCAST_TABLES_READY = True


def fetch_broadcast_targets(limit: int | None = None) -> list[BroadcastTarget]:
    """한 번이라도 대화한 적 있는 유저 전체가 대상. 수신거부는 별도로 관리하지 않고
    카카오톡 채널 차단 여부에 맡긴다(채널을 차단한 유저에게는 Event API가 자동으로 실패함)."""
    ensure_broadcast_tables()

    limit_clause = f"LIMIT {int(limit)}" if limit else ""
    rows = run_sql(
        f"""
        SELECT user_key, user_id_enc, last_seen_at
        FROM {CHAT_USERS_TABLE}
        ORDER BY last_seen_at DESC
        {limit_clause};
        """
    )

    targets: list[BroadcastTarget] = []
    for row in rows:
        try:
            user_id = decrypt_user_id(row["user_id_enc"])
        except Exception as exc:
            log.warning("[브로드캐스트] user_id 복호화 실패, 대상에서 제외 | user_key=%s... | %s", row["user_key"][:8], exc)
            continue
        if not user_id:
            continue
        targets.append(
            BroadcastTarget(user_key=row["user_key"], user_id=user_id, last_seen_at=row.get("last_seen_at"))
        )
    return targets


def fetch_already_sent_user_keys(event_name: str, run_date: date) -> set[str]:
    ensure_broadcast_tables()
    rows = run_sql(
        f"""
        SELECT DISTINCT user_key FROM {BROADCAST_SEND_LOG_TABLE}
        WHERE run_date = {_sql_literal(run_date)}
          AND event_name = {sql_quote(event_name)}
          AND status = 'SENT';
        """
    )
    return {row["user_key"] for row in rows}


def record_send_results(
    batch_id: UUID,
    run_date: date,
    event_name: str,
    chunk_index: int,
    results: list[SendLogRow],
) -> None:
    if not results:
        return
    ensure_broadcast_tables()

    values = ",\n".join(
        f"({_sql_literal(str(batch_id))}, {_sql_literal(run_date)}, {sql_quote(event_name)}, "
        f"{_sql_literal(row.user_key)}, {chunk_index}, {_sql_literal(row.http_status)}, "
        f"{_sql_literal(row.task_id)}, {sql_quote(row.status)}, {_sql_literal(row.error_message)})"
        for row in results
    )
    query = f"""
    INSERT INTO {BROADCAST_SEND_LOG_TABLE}
        (batch_id, run_date, event_name, user_key, chunk_index, http_status, task_id, status, error_message)
    VALUES
    {values}
    ON CONFLICT DO NOTHING;
    """
    run_sql(query)
