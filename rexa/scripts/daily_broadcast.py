"""매일 chat_users에 쌓인 사용자 전체에게 Kakao Event API로 먼저 메시지를 보내는 배치.

usage:
    python -m rexa.scripts.daily_broadcast [--dry-run] [--limit N] [--user-keys=k1,k2]
        [--event-name NAME] [--sleep-seconds 1.0] [--max-retries 3] [--force]

BROADCAST_ENABLED=true 로 설정되지 않으면 실제 Kakao API를 호출하지 않고 DRY_RUN으로만
기록한다(이중 안전장치). 광고성 메시지는 08:00~20:50(KST)에만 허용되므로, 이 시간대를
벗어나면 --force 없이는 중단한다.
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from rexa.infra.broadcast_store import (
    SendLogRow,
    fetch_already_sent_user_keys,
    fetch_broadcast_targets,
    record_send_results,
)
from rexa.infra.kakao_event import KakaoEventClient, KakaoEventError

log = logging.getLogger("rexa")

KST = timezone(timedelta(hours=9))
AD_MESSAGE_WINDOW_START = 8 * 60  # 08:00
AD_MESSAGE_WINDOW_END = 20 * 60 + 50  # 20:50

CHUNK_SIZE = 100
RETRY_BACKOFF_SECONDS = (2, 4, 8)


def _within_ad_message_window(now: datetime) -> bool:
    minutes = now.hour * 60 + now.minute
    return AD_MESSAGE_WINDOW_START <= minutes <= AD_MESSAGE_WINDOW_END


def _chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _load_env_config() -> dict[str, str]:
    bot_id = os.getenv("KAKAO_BOT_ID", "").strip()
    rest_api_key = os.getenv("KAKAO_BOT_REST_API_KEY", "").strip()
    if not rest_api_key:
        rest_api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
        if rest_api_key:
            log.warning("[브로드캐스트] KAKAO_BOT_REST_API_KEY 미설정, KAKAO_REST_API_KEY로 대체합니다.")

    missing = [name for name, value in (("KAKAO_BOT_ID", bot_id),) if not value]
    if not rest_api_key:
        missing.append("KAKAO_BOT_REST_API_KEY(or KAKAO_REST_API_KEY)")
    if missing:
        raise SystemExit(f"[브로드캐스트] 필수 환경변수 누락: {', '.join(missing)}")

    return {"bot_id": bot_id, "rest_api_key": rest_api_key}


def _send_chunk_with_retry(
    client: KakaoEventClient,
    event_name: str,
    user_keys: list[str],
    user_ids: list[str],
    max_retries: int,
) -> list[SendLogRow]:
    attempt = 0
    while True:
        try:
            result = client.send_event(event_name=event_name, user_ids=user_ids)
            return [
                SendLogRow(user_key=uk, status="SENT", http_status=result.http_status, task_id=result.task_id)
                for uk in user_keys
            ]
        except KakaoEventError as exc:
            message = str(exc)
            is_retryable = "status=429" in message or any(f"status=5{d}" in message for d in "0123456789")
            if not is_retryable or attempt >= max_retries:
                log.warning("[브로드캐스트] 청크 발송 실패(재시도 종료) | %s", message)
                return [
                    SendLogRow(user_key=uk, status="FAILED", error_message=message) for uk in user_keys
                ]
            delay = RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)]
            log.warning("[브로드캐스트] 청크 발송 실패, %d초 후 재시도(%d/%d) | %s", delay, attempt + 1, max_retries, message)
            time.sleep(delay)
            attempt += 1


def run_broadcast(
    dry_run: bool,
    limit: int | None,
    user_keys_filter: set[str] | None,
    event_name: str,
    sleep_seconds: float,
    max_retries: int,
    force: bool,
) -> None:
    if not event_name:
        raise SystemExit("[브로드캐스트] event_name이 비어 있습니다 (--event-name 또는 KAKAO_EVENT_NAME env 필요).")

    now_kst = datetime.now(KST)
    if not force and not _within_ad_message_window(now_kst):
        log.warning(
            "[브로드캐스트] 현재 시각(%s KST)이 광고성 메시지 허용 시간대(08:00~20:50)를 벗어나 중단합니다. "
            "--force로 우회 가능.",
            now_kst.strftime("%H:%M"),
        )
        return

    config = _load_env_config()
    broadcast_enabled = os.getenv("BROADCAST_ENABLED", "false").strip().lower() == "true"
    if not dry_run and not broadcast_enabled:
        log.warning("[브로드캐스트] BROADCAST_ENABLED가 true가 아니므로 dry-run으로 동작합니다.")
        dry_run = True

    targets = fetch_broadcast_targets(limit=limit)
    if user_keys_filter:
        targets = [t for t in targets if t.user_key in user_keys_filter]

    run_date = date.today()
    already_sent = fetch_already_sent_user_keys(event_name, run_date)
    targets = [t for t in targets if t.user_key not in already_sent]

    if not targets:
        log.info("[브로드캐스트] 대상자 없음, 종료")
        return

    log.info("[브로드캐스트] 시작 | event=%s | 대상 %d명 | dry_run=%s", event_name, len(targets), dry_run)

    timeout = int(os.getenv("KAKAO_EVENT_TIMEOUT_SECONDS", "10"))
    client = KakaoEventClient(bot_id=config["bot_id"], rest_api_key=config["rest_api_key"], timeout=timeout)
    batch_id = uuid4()
    total_sent = total_failed = 0

    for chunk_index, chunk in enumerate(_chunked(targets, CHUNK_SIZE)):
        user_keys = [t.user_key for t in chunk]
        user_ids = [t.user_id for t in chunk]

        if dry_run:
            results = [SendLogRow(user_key=uk, status="DRY_RUN") for uk in user_keys]
        else:
            results = _send_chunk_with_retry(client, event_name, user_keys, user_ids, max_retries)

        record_send_results(batch_id, run_date, event_name, chunk_index, results)
        total_sent += sum(1 for r in results if r.status in ("SENT", "DRY_RUN"))
        total_failed += sum(1 for r in results if r.status == "FAILED")

        time.sleep(sleep_seconds)

    log.info(
        "[브로드캐스트] 완료 | 총 대상 %d | 성공(발송/dry-run) %d | 실패 %d",
        len(targets),
        total_sent,
        total_failed,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="매일 chat_users 전체에게 Kakao Event API로 메시지 발송")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--user-keys", type=str, default=None, help="콤마로 구분된 user_key 목록(테스트용)")
    parser.add_argument("--event-name", type=str, default=None)
    parser.add_argument(
        "--sleep-seconds", type=float, default=float(os.getenv("KAKAO_EVENT_CHUNK_DELAY_SECONDS", "1.0"))
    )
    parser.add_argument("--max-retries", type=int, default=int(os.getenv("KAKAO_EVENT_MAX_RETRIES", "3")))
    parser.add_argument("--force", action="store_true", help="광고 메시지 허용 시간대 가드 우회")
    args = parser.parse_args()

    event_name = args.event_name or os.getenv("KAKAO_EVENT_NAME", "").strip()
    user_keys_filter = set(args.user_keys.split(",")) if args.user_keys else None

    run_broadcast(
        dry_run=args.dry_run,
        limit=args.limit,
        user_keys_filter=user_keys_filter,
        event_name=event_name,
        sleep_seconds=args.sleep_seconds,
        max_retries=args.max_retries,
        force=args.force,
    )


if __name__ == "__main__":
    main()
