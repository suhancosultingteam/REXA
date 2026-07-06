from datetime import date
from uuid import uuid4

import rexa.infra.broadcast_store as broadcast_store
from rexa.infra.broadcast_store import SendLogRow


def test_fetch_broadcast_targets_decrypts_and_skips_failures(monkeypatch):
    monkeypatch.setattr(broadcast_store, "ensure_broadcast_tables", lambda: None)

    rows = [
        {"user_key": "key-good", "user_id_enc": "enc-good", "last_seen_at": "2026-07-01 00:00:00+00"},
        {"user_key": "key-bad", "user_id_enc": "enc-bad", "last_seen_at": "2026-07-01 00:00:00+00"},
    ]
    monkeypatch.setattr(broadcast_store, "run_sql", lambda query: rows)

    def fake_decrypt(value):
        if value == "enc-bad":
            raise ValueError("복호화 실패")
        return "real-user-id"

    monkeypatch.setattr(broadcast_store, "decrypt_user_id", fake_decrypt)

    targets = broadcast_store.fetch_broadcast_targets()

    assert len(targets) == 1
    assert targets[0].user_key == "key-good"
    assert targets[0].user_id == "real-user-id"


def test_fetch_broadcast_targets_empty(monkeypatch):
    monkeypatch.setattr(broadcast_store, "ensure_broadcast_tables", lambda: None)
    monkeypatch.setattr(broadcast_store, "run_sql", lambda query: [])

    assert broadcast_store.fetch_broadcast_targets() == []


def test_fetch_already_sent_user_keys(monkeypatch):
    monkeypatch.setattr(broadcast_store, "ensure_broadcast_tables", lambda: None)
    monkeypatch.setattr(
        broadcast_store, "run_sql", lambda query: [{"user_key": "a"}, {"user_key": "b"}]
    )

    result = broadcast_store.fetch_already_sent_user_keys("morning_greeting", date(2026, 7, 2))

    assert result == {"a", "b"}


def test_record_send_results_builds_insert_and_skips_when_empty(monkeypatch):
    monkeypatch.setattr(broadcast_store, "ensure_broadcast_tables", lambda: None)

    captured_queries = []
    monkeypatch.setattr(broadcast_store, "run_sql", lambda query: captured_queries.append(query))

    broadcast_store.record_send_results(uuid4(), date(2026, 7, 2), "morning_greeting", 0, [])
    assert captured_queries == []

    rows = [SendLogRow(user_key="k1", status="SENT", http_status=200, task_id="t1")]
    broadcast_store.record_send_results(uuid4(), date(2026, 7, 2), "morning_greeting", 0, rows)

    assert len(captured_queries) == 1
    assert "INSERT INTO" in captured_queries[0]
    assert "k1" in captured_queries[0]
