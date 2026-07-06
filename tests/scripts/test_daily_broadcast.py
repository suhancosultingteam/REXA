from datetime import datetime, timedelta, timezone

import rexa.scripts.daily_broadcast as daily_broadcast
from rexa.infra.kakao_event import EventSendResult, KakaoEventError

KST = timezone(timedelta(hours=9))


def test_chunked_splits_into_expected_sizes():
    chunks = list(daily_broadcast._chunked(list(range(250)), 100))
    assert [len(c) for c in chunks] == [100, 100, 50]


def test_within_ad_message_window():
    assert daily_broadcast._within_ad_message_window(datetime(2026, 7, 2, 8, 0, tzinfo=KST))
    assert daily_broadcast._within_ad_message_window(datetime(2026, 7, 2, 20, 50, tzinfo=KST))
    assert not daily_broadcast._within_ad_message_window(datetime(2026, 7, 2, 7, 59, tzinfo=KST))
    assert not daily_broadcast._within_ad_message_window(datetime(2026, 7, 2, 20, 51, tzinfo=KST))


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def send_event(self, event_name, user_ids, data=None, params=None):
        self.calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_send_chunk_with_retry_succeeds_immediately(monkeypatch):
    monkeypatch.setattr(daily_broadcast.time, "sleep", lambda s: None)
    client = _FakeClient([EventSendResult(http_status=200, task_id="t1", raw={})])

    results = daily_broadcast._send_chunk_with_retry(client, "evt", ["k1", "k2"], ["u1", "u2"], max_retries=3)

    assert all(r.status == "SENT" for r in results)
    assert client.calls == 1


def test_send_chunk_with_retry_recovers_after_retryable_error(monkeypatch):
    monkeypatch.setattr(daily_broadcast.time, "sleep", lambda s: None)
    client = _FakeClient(
        [
            KakaoEventError("이벤트 API 호출 실패 status=429 body={}"),
            EventSendResult(http_status=200, task_id="t2", raw={}),
        ]
    )

    results = daily_broadcast._send_chunk_with_retry(client, "evt", ["k1"], ["u1"], max_retries=3)

    assert all(r.status == "SENT" for r in results)
    assert client.calls == 2


def test_send_chunk_with_retry_gives_up_on_non_retryable_error(monkeypatch):
    monkeypatch.setattr(daily_broadcast.time, "sleep", lambda s: None)
    client = _FakeClient([KakaoEventError("이벤트 API 호출 실패 status=400 body={}")])

    results = daily_broadcast._send_chunk_with_retry(client, "evt", ["k1"], ["u1"], max_retries=3)

    assert all(r.status == "FAILED" for r in results)
    assert client.calls == 1


def test_send_chunk_with_retry_exhausts_retries(monkeypatch):
    monkeypatch.setattr(daily_broadcast.time, "sleep", lambda s: None)
    client = _FakeClient(
        [
            KakaoEventError("status=500 body={}"),
            KakaoEventError("status=500 body={}"),
            KakaoEventError("status=500 body={}"),
            KakaoEventError("status=500 body={}"),
        ]
    )

    results = daily_broadcast._send_chunk_with_retry(client, "evt", ["k1"], ["u1"], max_retries=3)

    assert all(r.status == "FAILED" for r in results)
    assert client.calls == 4
