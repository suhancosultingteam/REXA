import csv
import importlib
import io
import json
import os
import subprocess
from decimal import Decimal
from functools import lru_cache
from typing import Any, Callable

import httpx
from dotenv import load_dotenv

from rexa.infra.logger import setup_logger

load_dotenv()

log = setup_logger()

KAKAO_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_SEARCH_SIZE = int(os.getenv("KAKAO_SEARCH_SIZE", "3"))
KAKAO_ADDRESS_SEARCH_SIZE = int(os.getenv("KAKAO_ADDRESS_SEARCH_SIZE", "1"))
KAKAO_HTTP_TIMEOUT_SECONDS = float(os.getenv("KAKAO_HTTP_TIMEOUT_SECONDS", "10"))

DB_HOST = os.getenv("REXA_DB_HOST", os.getenv("PGHOST", "localhost"))
DB_PORT = os.getenv("REXA_DB_PORT", os.getenv("PGPORT", "5432"))
DB_NAME = os.getenv("REXA_DB_NAME", os.getenv("PGDATABASE", "rexa"))
DB_USER = os.getenv("REXA_DB_USER", os.getenv("PGUSER", "postgres"))
DB_PASSWORD = os.getenv("REXA_DB_PASSWORD", os.getenv("PGPASSWORD", ""))
DB_CONNECT_TIMEOUT_SECONDS = int(os.getenv("REXA_DB_CONNECT_TIMEOUT_SECONDS", "5"))
DB_STATEMENT_TIMEOUT_MS = int(os.getenv("REXA_DB_STATEMENT_TIMEOUT_MS", "15000"))
DB_LOCK_TIMEOUT_MS = int(os.getenv("REXA_DB_LOCK_TIMEOUT_MS", "5000"))
DB_COMMAND_TIMEOUT_SECONDS = int(os.getenv("REXA_DB_COMMAND_TIMEOUT_SECONDS", "20"))


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=_json_default)


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def build_address_query_candidates(address_query: str) -> list[str]:
    escaped_query = sql_quote(address_query)
    query = f"""
        select sido, sigungu_name, bjdong_name
        from bjd_code
        where bjdong_name is not null
          and position(bjdong_name in {escaped_query}) > 0
        group by sido, sigungu_name, bjdong_name
        order by length(bjdong_name) desc, sido, sigungu_name, bjdong_name
    """
    rows = run_sql(query)
    if not rows:
        return [address_query]

    matched_sigungu_names = {
        (row.get("sigungu_name") or "").strip()
        for row in rows
        if (row.get("sigungu_name") or "").strip() and (row.get("sigungu_name") or "").strip() in address_query
    }

    candidates: list[str] = []
    seen = {address_query}

    for row in rows:
        sido = (row.get("sido") or "").strip()
        sigungu_name = (row.get("sigungu_name") or "").strip()
        bjdong_name = (row.get("bjdong_name") or "").strip()
        if not bjdong_name or bjdong_name not in address_query:
            continue
        if matched_sigungu_names and sigungu_name not in matched_sigungu_names:
            continue

        suffix = address_query.split(bjdong_name, 1)[1].strip()
        prefix_parts = [part for part in (sido, sigungu_name, bjdong_name) if part]
        candidate = " ".join(prefix_parts)
        if suffix:
            candidate = f"{candidate} {suffix}"
        if candidate not in seen:
            candidates.append(candidate)
            seen.add(candidate)

    candidates.append(address_query)
    return candidates


def _build_lookup_payload(
    keyword: str,
    origin_query: str,
    candidate_query: str,
    doc: dict[str, Any],
) -> dict[str, Any]:
    # Kakao 주소 검색 응답은 일부 도로명/장소성 질의에서 address=null 이고
    # road_address 만 채워지는 경우가 있어 안전하게 fallback 한다.
    addr = doc.get("address") or doc.get("road_address") or {}
    sigungu_name = addr.get("region_2depth_name", "")
    bjdong_name = addr.get("region_3depth_name", "")
    b_code = addr.get("b_code", "") or ""
    bun = addr.get("main_address_no", "") or ""
    ji = addr.get("sub_address_no", "") or ""

    if not b_code and sigungu_name and bjdong_name:
        sigungu_code, bjdong_code = _lookup_bjd_codes(sigungu_name, bjdong_name)
    else:
        sigungu_code, bjdong_code = b_code[:5], b_code[5:]

    return {
        "keyword": keyword,
        "origin": origin_query,
        "query": candidate_query,
        "fullname": doc.get("address_name", ""),
        "sigungu_name": sigungu_name,
        "sigungu_code": sigungu_code,
        "bjdong_name": bjdong_name,
        "bjdong_code": bjdong_code,
        "bun": bun.zfill(4) if bun else "",
        "ji": ji.zfill(4) if ji else "",
        "lat": float(doc["y"]),
        "lng": float(doc["x"]),
    }


@lru_cache(maxsize=512)
def _lookup_bjd_names(sigungu_code: str, bjdong_code: str) -> tuple[str, str]:
    if not (sigungu_code and bjdong_code):
        return "", ""

    query = f"""
        SELECT sigungu_name, bjdong_name
        FROM bjd_code
        WHERE sigungu_code = {sql_quote(sigungu_code)}
          AND bjdong_code = {sql_quote(bjdong_code)}
        LIMIT 1
    """
    rows = run_sql(query)
    if not rows:
        return "", ""

    row = rows[0]
    return (row.get("sigungu_name") or "", row.get("bjdong_name") or "")


@lru_cache(maxsize=512)
def _lookup_bjd_codes(sigungu_name: str, bjdong_name: str) -> tuple[str, str]:
    if not (sigungu_name and bjdong_name):
        return "", ""

    query = f"""
        SELECT sigungu_code, bjdong_code
        FROM bjd_code
        WHERE sigungu_name = {sql_quote(sigungu_name)}
          AND bjdong_name = {sql_quote(bjdong_name)}
        LIMIT 1
    """
    rows = run_sql(query)
    if not rows:
        return "", ""

    row = rows[0]
    return (row.get("sigungu_code") or "", row.get("bjdong_code") or "")


@lru_cache(maxsize=64)
def lookup_sigungu_code(sigungu_name: str) -> str:
    if not sigungu_name:
        return ""

    query = f"""
        SELECT sigungu_code
        FROM bjd_code
        WHERE sigungu_name = {sql_quote(sigungu_name)}
        LIMIT 1
    """
    rows = run_sql(query)
    return (rows[0].get("sigungu_code") or "") if rows else ""


def _normalize_lookup_payload_to_primary_lot(payload: dict[str, Any]) -> dict[str, Any]:
    sigungu_code = str(payload.get("sigungu_code") or payload.get("gu_code") or "")
    bjdong_code = str(payload.get("bjdong_code") or payload.get("dong_code") or "")
    bun = str(payload.get("bun") or "")
    ji = str(payload.get("ji") or "0000")

    if not (sigungu_code and bjdong_code and bun):
        return payload

    query = f"""
        SELECT
            sigungu_code,
            bjdong_code,
            bun,
            ji,
            plat_plc,
            new_plat_plc
        FROM br_atch_jibun
        WHERE (
            sigungu_code = {sql_quote(sigungu_code)}
            AND bjdong_code = {sql_quote(bjdong_code)}
            AND bun = {sql_quote(bun)}
            AND ji = {sql_quote(ji)}
        ) OR (
            atch_sigungu_code = {sql_quote(sigungu_code)}
            AND atch_bjdong_code = {sql_quote(bjdong_code)}
            AND atch_bun = {sql_quote(bun)}
            AND atch_ji = {sql_quote(ji)}
        )
        ORDER BY
            CASE
                WHEN sigungu_code = {sql_quote(sigungu_code)}
                 AND bjdong_code = {sql_quote(bjdong_code)}
                 AND bun = {sql_quote(bun)}
                 AND ji = {sql_quote(ji)}
                THEN 0
                ELSE 1
            END,
            id
        LIMIT 1
    """
    rows = run_sql(query)
    if not rows:
        return payload

    row = rows[0]
    normalized = dict(payload)
    normalized_sigungu_code = str(row.get("sigungu_code") or sigungu_code)
    normalized_bjdong_code = str(row.get("bjdong_code") or bjdong_code)
    normalized["sigungu_code"] = normalized_sigungu_code
    normalized["bjdong_code"] = normalized_bjdong_code
    normalized["bun"] = normalize_lot(row.get("bun"), default=bun)
    normalized["ji"] = normalize_lot(row.get("ji"), default=ji)

    sigungu_name, bjdong_name = _lookup_bjd_names(normalized_sigungu_code, normalized_bjdong_code)
    if sigungu_name:
        normalized["sigungu_name"] = sigungu_name
    if bjdong_name:
        normalized["bjdong_name"] = bjdong_name

    fullname = (row.get("new_plat_plc") or row.get("plat_plc") or "").strip()
    if fullname:
        normalized["fullname"] = fullname

    return normalized


def lookup_addresses(keyword: str, address_queries: str | list[str]) -> dict[str, Any]:
    raw_queries = [address_queries] if isinstance(address_queries, str) else address_queries
    seen_queries: set[str] = set()

    for raw_query in raw_queries:
        if not raw_query:
            continue
        for candidate_query in build_address_query_candidates(raw_query):
            if candidate_query in seen_queries:
                continue
            seen_queries.add(candidate_query)

            try:
                log.debug(
                    f"[툴][lookup_addresses] Kakao 주소 검색 ▶ "
                    f"keyword={keyword!r} origin={raw_query!r} candidate={candidate_query!r}"
                )
                res = httpx.get(
                    "https://dapi.kakao.com/v2/local/search/address.json",
                    headers={"Authorization": f"KakaoAK {KAKAO_KEY}"},
                    params={"query": candidate_query, "size": KAKAO_ADDRESS_SEARCH_SIZE},
                    timeout=KAKAO_HTTP_TIMEOUT_SECONDS,
                )
            except httpx.TimeoutException:
                log.error(
                    f"[툴][lookup_addresses] Kakao 주소 API 타임아웃 | "
                    f"keyword={keyword!r} candidate={candidate_query!r} timeout={KAKAO_HTTP_TIMEOUT_SECONDS}s"
                )
                return error_result(
                    f"Kakao 주소 API 타임아웃: query={candidate_query} timeout={KAKAO_HTTP_TIMEOUT_SECONDS}s"
                )
            except httpx.HTTPError as exc:
                log.error(
                    f"[툴][lookup_addresses] Kakao 주소 API 연결 실패 | "
                    f"keyword={keyword!r} candidate={candidate_query!r} error={exc}"
                )
                return error_result(f"Kakao 주소 API 연결 실패: {exc}")

            if res.status_code != 200:
                log.error(
                    f"[툴][lookup_addresses] Kakao 주소 API 오류 "
                    f"status={res.status_code} | candidate={candidate_query!r} | body={res.text[:300]}"
                )
                return error_result(f"Kakao 주소 API {res.status_code}: {res.text[:200]}")

            try:
                docs = res.json().get("documents", [])
            except Exception as exc:
                log.error(
                    f"[툴][lookup_addresses] Kakao 주소 응답 파싱 실패 | "
                    f"candidate={candidate_query!r} | body={res.text[:300]} | error={exc}"
                )
                return error_result(f"Kakao 주소 응답 파싱 실패: {exc}")

            if not docs:
                continue

            payload = _build_lookup_payload(keyword, raw_query, candidate_query, docs[0])
            return _normalize_lookup_payload_to_primary_lot(payload)

    joined_queries = ", ".join(raw_queries)
    return {"error": f"{joined_queries}를 찾을 수 없음"}


def lookup_address(keyword: str, address_query: str) -> dict[str, Any]:
    return lookup_addresses(keyword, address_query)


def run_sql(query: str) -> list[dict[str, str]]:
    cmd = [
        "psql",
        "-X",
        "-h",
        DB_HOST,
        "-p",
        DB_PORT,
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-w",
        "-v",
        "ON_ERROR_STOP=1",
        "--csv",
        "-c",
        query,
    ]
    env = os.environ.copy()
    if DB_PASSWORD:
        env["PGPASSWORD"] = DB_PASSWORD
    env["PGCONNECT_TIMEOUT"] = str(DB_CONNECT_TIMEOUT_SECONDS)
    env["PGOPTIONS"] = (
        f"-c statement_timeout={DB_STATEMENT_TIMEOUT_MS} "
        f"-c lock_timeout={DB_LOCK_TIMEOUT_MS}"
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=DB_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "DB 쿼리 타임아웃 "
            f"({DB_COMMAND_TIMEOUT_SECONDS}s) — host={DB_HOST}:{DB_PORT} db={DB_NAME} "
            f"connect_timeout={DB_CONNECT_TIMEOUT_SECONDS}s statement_timeout={DB_STATEMENT_TIMEOUT_MS}ms"
        )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "SQL 실행 실패"
        raise RuntimeError(message)

    output = result.stdout.strip()
    if not output:
        return []
    return list(csv.DictReader(io.StringIO(output)))


def error_result(message: str, **extra: Any) -> dict[str, Any]:
    payload = {"error": message}
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


def normalize_sigungu_code(value: str) -> str:
    digits = digits_only(value)
    return digits[:5]


def normalize_bjdong_code(value: str) -> str:
    digits = digits_only(value)
    if len(digits) >= 5:
        return digits[-5:]
    return digits


def normalize_gu_code(value: str) -> str:
    return normalize_sigungu_code(value)


def normalize_dong_code(value: str) -> str:
    return normalize_bjdong_code(value)


def normalize_lot(value: str | int | None, width: int = 4, default: str = "0000") -> str:
    if value is None:
        return default
    digits = digits_only(str(value))
    if not digits:
        return default
    return digits.zfill(width)


def digits_only(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


KUMHA_BUILDING_CODE = "P1761726365421"


def _truncate_address(value: str | None) -> str | None:
    if value is None:
        return None

    parts = value.strip().split()
    if len(parts) <= 3:
        return value

    return " ".join(parts[:3])


mask_jibun_address = _truncate_address
mask_road_address = _truncate_address


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def parse_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    return int(value)


def parse_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    return float(value)


def format_human_krw(amount: Any) -> str:
    """원 단위 금액을 사람이 읽기 쉬운 한국식 단위 문자열로 변환합니다.

    예:
    - 349102267607 -> "3491 억"
    - 349102267 -> "3.5 억"
    - 15340000 -> "1534 만"
    - 153400 -> "15.3 만"
    """
    amount_int = parse_int(amount)
    if amount_int is None:
        return "-"
    if amount_int == 0:
        return "0원"

    sign = "-" if amount_int < 0 else ""
    abs_amount = abs(amount_int)

    for unit_name, unit_value in (("조", 1_0000_0000_0000), ("억", 100_000_000), ("만", 10_000)):
        if abs_amount < unit_value:
            continue

        scaled = abs_amount / unit_value
        if scaled >= 100:
            display = str(round(scaled))
        else:
            display = f"{scaled:.1f}".rstrip("0").rstrip(".")
        return f"{sign}{display} {unit_name}"

    return f"{sign}{abs_amount:,}"


def serialize_krw(amount: Any) -> dict[str, Any]:
    amount_float = parse_float(amount)
    amount_krw = None if amount_float is None else round(amount_float)
    return {
        "krw": amount_krw,
        "human": format_human_krw(amount_krw),
    }


def load_commercial_area_backend() -> Callable[[str, list[str]], Any] | None:
    import_path = os.getenv("COMMERCIAL_AREA_SEARCH_FUNC", "").strip()
    if not import_path:
        return None

    module_name, separator, attr_name = import_path.partition(":")
    if not separator:
        raise RuntimeError("COMMERCIAL_AREA_SEARCH_FUNC must be '<module>:<callable>' 형식이어야 합니다.")

    module = importlib.import_module(module_name)
    backend = getattr(module, attr_name, None)
    if backend is None or not callable(backend):
        raise RuntimeError(f"상권 분석 백엔드 {import_path} 를 불러올 수 없습니다.")
    return backend
