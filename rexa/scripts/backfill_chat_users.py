"""chat_logs에 이미 쌓인 과거 user_id를 chat_users 레지스트리로 1회성 백필한다.

chat_users는 배포 이후 실시간 upsert로 채워지므로(rexa/infra/chat_logging.py의
save_chat_log), 이 스크립트는 배포 직후 딱 한 번만 실행하면 된다. 이후로는
chat_logs 전체를 스캔할 필요가 없다.

usage: python -m rexa.scripts.backfill_chat_users [--dry-run] [--batch-size N]
"""

from __future__ import annotations

import argparse
import logging

from rexa.infra.chat_logging import (
    CHAT_LOG_TABLE,
    CHAT_USERS_TABLE,
    _sql_literal,
    ensure_chat_log_table,
    ensure_chat_users_table,
    run_sql,
)

log = logging.getLogger("rexa")

DEFAULT_BATCH_SIZE = 500


def _fetch_distinct_users() -> list[dict[str, str]]:
    return run_sql(
        f"""
        SELECT DISTINCT ON (user_key) user_key, user_id_enc, created_at
        FROM {CHAT_LOG_TABLE}
        WHERE user_id_enc IS NOT NULL AND user_key IS NOT NULL
        ORDER BY user_key, created_at DESC;
        """
    )


def _insert_batch(rows: list[dict[str, str]]) -> None:
    values = ",\n".join(
        f"({_sql_literal(row['user_key'])}, {_sql_literal(row['user_id_enc'])}, "
        f"{_sql_literal(row['created_at'])}, {_sql_literal(row['created_at'])})"
        for row in rows
    )
    query = f"""
    INSERT INTO {CHAT_USERS_TABLE} (user_key, user_id_enc, first_seen_at, last_seen_at)
    VALUES
    {values}
    ON CONFLICT (user_key) DO NOTHING;
    """
    run_sql(query)


def backfill(dry_run: bool = False, batch_size: int = DEFAULT_BATCH_SIZE) -> int:
    ensure_chat_log_table()
    ensure_chat_users_table()

    rows = _fetch_distinct_users()
    log.info("[백필] chat_logs에서 고유 user_key %d명 발견", len(rows))

    if dry_run:
        log.info("[백필] dry-run 모드, 실제 INSERT는 건너뜁니다.")
        return len(rows)

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        _insert_batch(batch)
        log.info("[백필] %d/%d 건 처리 완료", min(i + batch_size, len(rows)), len(rows))

    log.info("[백필] 완료 | 총 %d명 chat_users에 반영", len(rows))
    return len(rows)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="chat_logs -> chat_users 1회성 백필")
    parser.add_argument("--dry-run", action="store_true", help="실제 INSERT 없이 대상자 수만 확인")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    backfill(dry_run=args.dry_run, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
