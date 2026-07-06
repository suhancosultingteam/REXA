"""가지고 있는 카카오 user_id에게 Kakao Event API로 바로 메시지를 발송하는 단발성 스크립트.

DB 조회나 옵트아웃/중복발송 체크 없이 넘겨준 user_id에 대해서만 즉시 호출한다.

usage:
    python -m rexa.scripts.send_kakao_event <user_id> [<user_id> ...] --event-name NAME
    python -m rexa.scripts.send_kakao_event u1,u2,u3 --event-name NAME
"""

from __future__ import annotations

import argparse
import json
import logging
import os

from rexa.infra.kakao_event import KakaoEventClient, KakaoEventError

log = logging.getLogger("rexa")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="주어진 user_id에게 Kakao Event API로 즉시 발송")
    parser.add_argument("user_ids", nargs="+", help="카카오 user_id (공백 또는 콤마로 여러 개 지정 가능)")
    parser.add_argument("--event-name", default=os.getenv("KAKAO_EVENT_NAME", "").strip())
    parser.add_argument("--data", default=None, help="event.data로 보낼 JSON 문자열 (선택)")
    args = parser.parse_args()

    user_ids: list[str] = []
    for raw in args.user_ids:
        user_ids.extend(uid.strip() for uid in raw.split(",") if uid.strip())

    if not args.event_name:
        raise SystemExit("--event-name 이 필요합니다 (또는 KAKAO_EVENT_NAME env 설정).")
    if len(user_ids) > 100:
        raise SystemExit(f"Event API는 1회 요청당 최대 100명까지만 가능합니다 (입력: {len(user_ids)}명).")

    bot_id = os.getenv("KAKAO_BOT_ID", "").strip()
    rest_api_key = os.getenv("KAKAO_BOT_REST_API_KEY", "").strip() or os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not bot_id or not rest_api_key:
        raise SystemExit("KAKAO_BOT_ID / KAKAO_BOT_REST_API_KEY(or KAKAO_REST_API_KEY) 환경변수가 필요합니다.")

    data = json.loads(args.data) if args.data else None

    client = KakaoEventClient(bot_id=bot_id, rest_api_key=rest_api_key)
    try:
        result = client.send_event(event_name=args.event_name, user_ids=user_ids, data=data)
    except KakaoEventError as exc:
        raise SystemExit(f"발송 실패: {exc}") from exc

    log.info("[발송완료] event=%s | 대상 %d명 | taskId=%s", args.event_name, len(user_ids), result.task_id)
    print(f"taskId={result.task_id} status={result.http_status}")


if __name__ == "__main__":
    main()
