import rexa.infra.chat_logging as chat_logging


def test_upsert_chat_user_skips_when_missing_values(monkeypatch):
    calls = []
    monkeypatch.setattr(chat_logging, "run_sql", lambda query: calls.append(query))
    monkeypatch.setattr(chat_logging, "ensure_chat_users_table", lambda: None)

    chat_logging.upsert_chat_user(None, "enc")
    chat_logging.upsert_chat_user("key", None)

    assert calls == []


def test_upsert_chat_user_builds_upsert_query(monkeypatch):
    calls = []
    monkeypatch.setattr(chat_logging, "run_sql", lambda query: calls.append(query))
    monkeypatch.setattr(chat_logging, "ensure_chat_users_table", lambda: None)

    chat_logging.upsert_chat_user("hash-key", "enc-value")

    assert len(calls) == 1
    query = calls[0]
    assert "INSERT INTO" in query
    assert "hash-key" in query
    assert "enc-value" in query
    assert "ON CONFLICT (user_key) DO UPDATE" in query
