from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import base64
import csv
import hashlib
import io
import json
import logging
import os
import subprocess
from typing import Any
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv


load_dotenv()

log = logging.getLogger("rexa")

CHAT_LOG_TABLE = os.getenv("CHAT_LOG_TABLE", "chat_logs").strip() or "chat_logs"
CHAT_LOG_USER_HASH_SALT = os.getenv("CHAT_LOG_USER_HASH_SALT", "")
CHAT_LOG_USER_ID_ENC_KEY = os.getenv("CHAT_LOG_USER_ID_ENC_KEY", "")
CHAT_USERS_TABLE = os.getenv("CHAT_USERS_TABLE", "chat_users").strip() or "chat_users"

_TABLE_READY = False
_CHAT_USERS_TABLE_READY = False


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def run_sql(query: str) -> list[dict[str, str]]:
    db_host = os.getenv("REXA_DB_HOST", os.getenv("PGHOST", "localhost"))
    db_port = os.getenv("REXA_DB_PORT", os.getenv("PGPORT", "5432"))
    db_name = os.getenv("REXA_DB_NAME", os.getenv("PGDATABASE", "rexa"))
    db_user = os.getenv("REXA_DB_USER", os.getenv("PGUSER", "postgres"))
    db_password = os.getenv("REXA_DB_PASSWORD", os.getenv("PGPASSWORD", ""))

    cmd = [
        "psql",
        "-h",
        db_host,
        "-p",
        db_port,
        "-U",
        db_user,
        "-d",
        db_name,
        "-w",
        "--csv",
        "-c",
        query,
    ]
    env = os.environ.copy()
    if db_password:
        env["PGPASSWORD"] = db_password

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "SQL 실행 실패"
        raise RuntimeError(message)

    output = result.stdout.strip()
    if not output:
        return []
    return list(csv.DictReader(io.StringIO(output)))


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class LayerMetrics:
    provider: str = ""
    model_name: str = ""
    latency_ms: int = 0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    timing_breakdown: dict[str, int] = field(default_factory=dict)

    def token_payload(self) -> dict[str, Any]:
        payload = self.tokens.to_dict()
        if self.provider:
            payload["provider"] = self.provider
        if self.model_name:
            payload["model_name"] = self.model_name
        return payload

    def timing_payload(self) -> dict[str, int]:
        payload = {"total_ms": self.latency_ms}
        payload.update(self.timing_breakdown)
        return payload


@dataclass
class PipelineRunResult:
    user_input: str
    answer: str
    user_id: str | None = None
    request_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    provider: str = ""
    model_name: str = ""
    status: str = "success"
    total_latency_ms: int = 0
    total_tokens: int = 0
    layer_metrics: dict[str, LayerMetrics] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def finalize(self) -> None:
        self.total_tokens = sum(metric.tokens.total_tokens for metric in self.layer_metrics.values())
        if not self.provider:
            for layer_name in ("answer", "router", "preprocess"):
                metric = self.layer_metrics.get(layer_name)
                if metric and metric.provider:
                    self.provider = metric.provider
                    self.model_name = metric.model_name
                    break

    @property
    def layer_latency_payload(self) -> dict[str, int]:
        return {name: metric.latency_ms for name, metric in self.layer_metrics.items()}

    @property
    def layer_tokens_payload(self) -> dict[str, dict[str, Any]]:
        return {name: metric.token_payload() for name, metric in self.layer_metrics.items()}

    @property
    def layer_timing_payload(self) -> dict[str, dict[str, int]]:
        return {name: metric.timing_payload() for name, metric in self.layer_metrics.items()}


def _as_int(value: Any) -> int:
    if value in (None, "", False):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _extract_cache_read_tokens(payload: dict[str, Any]) -> int:
    details = payload.get("input_token_details") or payload.get("input_tokens_details") or {}
    return _as_int(
        details.get("cache_read")
        or details.get("cached_tokens")
        or payload.get("cache_read_input_tokens")
        or payload.get("cache_read_tokens")
    )


def _extract_cache_write_tokens(payload: dict[str, Any]) -> int:
    details = payload.get("input_token_details") or payload.get("input_tokens_details") or {}
    return _as_int(
        details.get("cache_creation")
        or payload.get("cache_creation_input_tokens")
        or payload.get("cache_write_tokens")
    )


def extract_token_usage(message: Any) -> TokenUsage:
    usage_metadata = getattr(message, "usage_metadata", None) or {}
    response_metadata = getattr(message, "response_metadata", None) or {}
    candidates = [
        usage_metadata,
        response_metadata.get("usage") or {},
        response_metadata.get("token_usage") or {},
        response_metadata,
    ]

    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        input_tokens = input_tokens or _as_int(
            candidate.get("input_tokens")
            or candidate.get("prompt_tokens")
        )
        output_tokens = output_tokens or _as_int(
            candidate.get("output_tokens")
            or candidate.get("completion_tokens")
        )
        cache_read_tokens = cache_read_tokens or _extract_cache_read_tokens(candidate)
        cache_write_tokens = cache_write_tokens or _extract_cache_write_tokens(candidate)

    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
    )


def merge_token_usage(messages: list[Any]) -> TokenUsage:
    merged = TokenUsage()
    for message in messages:
        merged.add(extract_token_usage(message))
    return merged


def hash_user_id(user_id: str | None) -> str | None:
    if not user_id:
        return None
    digest = hashlib.sha256(f"{CHAT_LOG_USER_HASH_SALT}:{user_id}".encode("utf-8")).hexdigest()
    return digest


def _aes_key() -> bytes:
    if not CHAT_LOG_USER_ID_ENC_KEY:
        raise RuntimeError("CHAT_LOG_USER_ID_ENC_KEY 환경변수가 설정되어 있지 않습니다.")
    key = base64.b64decode(CHAT_LOG_USER_ID_ENC_KEY)
    if len(key) not in (16, 24, 32):
        raise RuntimeError("CHAT_LOG_USER_ID_ENC_KEY는 base64로 인코딩된 16/24/32바이트 키여야 합니다.")
    return key


def encrypt_user_id(user_id: str | None) -> str | None:
    """실제 user id가 필요한 운영 조회를 위해 AES-GCM으로 암호화해 반환한다 (nonce||ciphertext, base64)."""
    if not user_id:
        return None
    aesgcm = AESGCM(_aes_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, user_id.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_user_id(encrypted_value: str | None) -> str | None:
    if not encrypted_value:
        return None
    aesgcm = AESGCM(_aes_key())
    raw = base64.b64decode(encrypted_value)
    nonce, ciphertext = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def ensure_chat_log_table() -> None:
    global _TABLE_READY
    if _TABLE_READY:
        return

    run_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {CHAT_LOG_TABLE} (
            id BIGSERIAL PRIMARY KEY,
            request_id UUID NOT NULL UNIQUE,
            user_key VARCHAR(128),
            user_id_enc TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_input TEXT NOT NULL,
            model_output TEXT,
            provider VARCHAR(30),
            model_name VARCHAR(100),
            status VARCHAR(20) NOT NULL DEFAULT 'success',
            error_code VARCHAR(100),
            error_message TEXT,
            total_latency_ms INTEGER,
            total_tokens INTEGER,
            layer_latency JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            layer_tokens JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb
        );

        ALTER TABLE {CHAT_LOG_TABLE} ADD COLUMN IF NOT EXISTS user_id_enc TEXT;

        CREATE INDEX IF NOT EXISTS idx_{CHAT_LOG_TABLE}_user_created
            ON {CHAT_LOG_TABLE} (user_key, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_{CHAT_LOG_TABLE}_created_at
            ON {CHAT_LOG_TABLE} (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_{CHAT_LOG_TABLE}_provider_model
            ON {CHAT_LOG_TABLE} (provider, model_name);
        CREATE INDEX IF NOT EXISTS idx_{CHAT_LOG_TABLE}_status
            ON {CHAT_LOG_TABLE} (status);
        """
    )
    _TABLE_READY = True


def ensure_chat_users_table() -> None:
    """user_key당 1행만 유지하는 유저 레지스트리. 브로드캐스트 배치가 chat_logs 전체를
    스캔하지 않고 이 작은 테이블만 읽도록 하기 위함(메시지 저장 시마다 upsert)."""
    global _CHAT_USERS_TABLE_READY
    if _CHAT_USERS_TABLE_READY:
        return

    run_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {CHAT_USERS_TABLE} (
            user_key VARCHAR(128) PRIMARY KEY,
            user_id_enc TEXT NOT NULL,
            first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    _CHAT_USERS_TABLE_READY = True


def upsert_chat_user(user_key: str | None, user_id_enc: str | None) -> None:
    if not user_key or not user_id_enc:
        return
    ensure_chat_users_table()
    query = f"""
    INSERT INTO {CHAT_USERS_TABLE} (user_key, user_id_enc, first_seen_at, last_seen_at)
    VALUES ({_sql_literal(user_key)}, {_sql_literal(user_id_enc)}, NOW(), NOW())
    ON CONFLICT (user_key) DO UPDATE
    SET user_id_enc = EXCLUDED.user_id_enc, last_seen_at = NOW();
    """
    run_sql(query)


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return sql_quote(value.astimezone(timezone.utc).isoformat())
    if isinstance(value, (dict, list)):
        return f"{sql_quote(json_dumps(value))}::jsonb"
    return sql_quote(str(value))


def save_chat_log(result: PipelineRunResult) -> None:
    result.finalize()
    ensure_chat_log_table()

    metadata = dict(result.metadata)
    metadata["layer_models"] = {
        name: {
            "provider": metric.provider,
            "model_name": metric.model_name,
        }
        for name, metric in result.layer_metrics.items()
    }
    metadata["layer_timing"] = result.layer_timing_payload

    try:
        user_id_enc = encrypt_user_id(result.user_id)
    except RuntimeError as exc:
        user_id_enc = None
        log.warning("[로그] user_id 암호화 실패, user_id_enc는 NULL로 저장됩니다 | %s", exc)

    query = f"""
    INSERT INTO {CHAT_LOG_TABLE} (
        request_id,
        user_key,
        user_id_enc,
        created_at,
        user_input,
        model_output,
        provider,
        model_name,
        status,
        error_code,
        error_message,
        total_latency_ms,
        total_tokens,
        layer_latency,
        layer_tokens,
        metadata
    ) VALUES (
        {_sql_literal(result.request_id)},
        {_sql_literal(hash_user_id(result.user_id))},
        {_sql_literal(user_id_enc)},
        {_sql_literal(result.created_at)},
        {_sql_literal(result.user_input)},
        {_sql_literal(result.answer)},
        {_sql_literal(result.provider)},
        {_sql_literal(result.model_name)},
        {_sql_literal(result.status)},
        {_sql_literal(result.error_code)},
        {_sql_literal(result.error_message)},
        {_sql_literal(result.total_latency_ms)},
        {_sql_literal(result.total_tokens)},
        {_sql_literal(result.layer_latency_payload)},
        {_sql_literal(result.layer_tokens_payload)},
        {_sql_literal(metadata)}
    )
    ON CONFLICT (request_id) DO NOTHING;
    """
    run_sql(query)

    try:
        upsert_chat_user(hash_user_id(result.user_id), user_id_enc)
    except Exception as exc:
        log.warning("[로그] chat_users upsert 실패 | request_id=%s | %s", result.request_id, exc)


def save_chat_log_best_effort(result: PipelineRunResult) -> None:
    try:
        save_chat_log(result)
    except Exception as exc:
        log.warning("[로그] chat log 저장 실패 | request_id=%s | %s", result.request_id, exc)
