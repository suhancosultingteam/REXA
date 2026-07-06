"""Kakao i 오픈빌더 Event API 클라이언트.

봇이 사용자에게 먼저 메시지를 보내는(푸시) 용도. `rexa/entrypoints/kakao_callback.py`의
KakaoCallbackClient(1회성 callbackUrl 응답용)와는 별개의 API.

https://kakaobusiness.gitbook.io/main/tool/chatbot/main_notions/event-api
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import logging

import requests

log = logging.getLogger("rexa")

KAKAO_EVENT_API_MAX_USERS_PER_REQUEST = 100


class KakaoEventError(Exception):
    pass


@dataclass
class EventSendResult:
    http_status: int
    task_id: str | None
    raw: dict[str, Any]


class KakaoEventClient:
    def __init__(self, bot_id: str, rest_api_key: str, timeout: int = 10):
        self.bot_id = bot_id
        self.rest_api_key = rest_api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"KakaoAK {self.rest_api_key}",
            "Content-Type": "application/json",
        }

    def send_event(
        self,
        event_name: str,
        user_ids: list[str],
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> EventSendResult:
        if not user_ids:
            raise KakaoEventError("user_ids가 비어 있습니다.")
        if len(user_ids) > KAKAO_EVENT_API_MAX_USERS_PER_REQUEST:
            raise KakaoEventError(
                f"1회 요청당 최대 {KAKAO_EVENT_API_MAX_USERS_PER_REQUEST}명까지만 발송 가능합니다 "
                f"(요청: {len(user_ids)}명)."
            )

        url = f"https://bot-api.kakao.com/v2/bots/{self.bot_id}/talk"
        body: dict[str, Any] = {
            "event": {"name": event_name, "data": data or {}},
            "user": [{"type": "botUserKey", "id": uid} for uid in user_ids],
        }
        if params:
            body["params"] = params

        log.info("[카카오이벤트] 발송 요청 | event=%s | 대상 %d명", event_name, len(user_ids))
        try:
            resp = requests.post(url, json=body, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as exc:
            raise KakaoEventError(f"이벤트 API 요청 실패: {exc}") from exc

        try:
            raw = resp.json()
        except Exception as exc:
            raise KakaoEventError(
                f"이벤트 API 응답이 JSON이 아닙니다. status={resp.status_code}, body={resp.text}"
            ) from exc

        if resp.status_code >= 400:
            raise KakaoEventError(
                f"이벤트 API 호출 실패 status={resp.status_code} body={raw}"
            )

        task_id = raw.get("taskId")
        log.info("[카카오이벤트] 발송 접수 완료 | event=%s | taskId=%s", event_name, task_id)
        return EventSendResult(http_status=resp.status_code, task_id=task_id, raw=raw)

    def get_task_result(self, task_id: str) -> dict[str, Any]:
        url = f"https://bot-api.kakao.com/v1/tasks/{task_id}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as exc:
            raise KakaoEventError(f"발송 결과 조회 실패: {exc}") from exc

        try:
            raw = resp.json()
        except Exception as exc:
            raise KakaoEventError(
                f"발송 결과 응답이 JSON이 아닙니다. status={resp.status_code}, body={resp.text}"
            ) from exc

        if resp.status_code >= 400:
            raise KakaoEventError(f"발송 결과 조회 실패 status={resp.status_code} body={raw}")
        return raw
