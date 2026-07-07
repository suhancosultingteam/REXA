import os

import httpx
from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._utils import error_result
from rexa.tools.search_commercial_area.search_commercial_area_chunk_dto import SearchCommercialAreaChunkDto
from rexa.tools.search_commercial_area.search_commercial_area_input_dto import SearchCommercialAreaInputDto
from rexa.tools.search_commercial_area.search_commercial_area_result_dto import SearchCommercialAreaResultDto

BOS_SERVER_BASE_URL = os.getenv("BOS_SERVER_BASE_URL", "http://localhost:10000").rstrip("/")
COMMERCIAL_AREA_TOP_K = int(os.getenv("COMMERCIAL_AREA_TOP_K", "3"))
COMMERCIAL_AREA_MAX_QUERIES = int(os.getenv("COMMERCIAL_AREA_MAX_QUERIES", "3"))
COMMERCIAL_AREA_TIMEOUT_SECONDS = float(os.getenv("COMMERCIAL_AREA_TIMEOUT_SECONDS", "20"))
log = setup_logger()


_GENERIC_COMMERCIAL_SUFFIXES = (
    "상권 분석",
    "상권분석",
    "상권",
)


def _normalize_query_text(query: str) -> str:
    return " ".join(query.strip().split())


def _subject_without_generic_suffix(query: str) -> str:
    normalized = _normalize_query_text(query)
    for suffix in _GENERIC_COMMERCIAL_SUFFIXES:
        if normalized.endswith(suffix):
            return normalized[:-len(suffix)].strip()
    return normalized


def _is_generic_commercial_query(query: str) -> bool:
    normalized = _normalize_query_text(query)
    return any(normalized.endswith(suffix) for suffix in _GENERIC_COMMERCIAL_SUFFIXES)


def _build_search_queries(queries: list[str]) -> list[str]:
    normalized_all: list[str] = []
    seen: set[str] = set()
    for query in queries:
        value = _normalize_query_text(query)
        if not value or value in seen:
            continue
        seen.add(value)
        normalized_all.append(value)

    if not normalized_all:
        return []

    filtered: list[str] = []
    for query in normalized_all:
        if _is_generic_commercial_query(query):
            subject = _subject_without_generic_suffix(query)
            has_more_specific_query = any(
                other != query and _normalize_query_text(other).startswith(subject)
                for other in normalized_all
            )
            if has_more_specific_query:
                continue
        filtered.append(query)

    source = filtered or normalized_all
    limit = max(1, COMMERCIAL_AREA_MAX_QUERIES)
    return source[:limit]


def _search_chunks(query: str, top_k: int, sigungu_code: str) -> list[dict]:
    response = httpx.get(
        f"{BOS_SERVER_BASE_URL}/commercial-area-reports/chunks/search",
        params={"query": query, "topK": top_k, "sigunguCode": sigungu_code},
        timeout=COMMERCIAL_AREA_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("rows", [])


def _normalize_chunk_row(row: dict, matched_query: str) -> dict:
    payload = dict(row)
    payload["matched_query"] = matched_query
    payload["chunk_uuid"] = (
        payload.get("chunk_uuid")
        or payload.get("chunkUuid")
        or payload.get("id")
    )
    payload["score"] = (
        payload.get("score")
        or payload.get("similarity")
        or payload.get("searchScore")
        or payload.get("@search.score")
    )
    payload["text"] = (
        payload.get("text")
        or payload.get("chunkText")
        or payload.get("chunk_text")
        or payload.get("content")
        or payload.get("body")
        or payload.get("summary")
        or ""
    )
    payload["district"] = (
        payload.get("district")
        or payload.get("sigungu_name")
        or payload.get("sigunguName")
    )
    return payload


@tool(args_schema=SearchCommercialAreaInputDto)
def search_commercial_area(sigungu_code: str, queries: list[str]) -> SearchCommercialAreaResultDto:
    """구 단위 상권 분석 보고서를 벡터 검색합니다.

    사용 시점:
    - 상권, 유동인구, 업종 분포, 생존률, 입지 평가 질문
    - 주소가 구 단위인 경우

    파라미터:
    - `sigungu_code`: 조회 대상 구의 5자리 시군구 코드
    - `queries`: 보고서 검색용 자연어 쿼리 배열

    반환:
    - `sigungu_code`, `queries`, `count`, `chunks`
    """
    log.info(f"[툴][search_commercial_area] 시작 ▶ sigungu_code={sigungu_code!r} | queries={queries} | BOS_URL={BOS_SERVER_BASE_URL}")

    if not sigungu_code:
        log.error("[툴][search_commercial_area] sigungu_code 없음")
        return SearchCommercialAreaResultDto(error="상권 분석 조회에는 sigungu_code 가 필요합니다.")
    if not queries:
        log.error(f"[툴][search_commercial_area] queries 없음 | sigungu_code={sigungu_code!r}")
        return SearchCommercialAreaResultDto(error="상권 분석 조회에는 queries 배열이 필요합니다.", sigungu_code=sigungu_code)

    search_queries = _build_search_queries(queries)
    log.debug(f"[툴][search_commercial_area] 검색 쿼리 구성 완료: {search_queries}")

    if not search_queries:
        log.error(f"[툴][search_commercial_area] 유효 쿼리 없음 | sigungu_code={sigungu_code!r} | queries={queries}")
        return SearchCommercialAreaResultDto(error="유효한 검색 쿼리가 없습니다.", sigungu_code=sigungu_code, queries=queries)

    chunks: list[SearchCommercialAreaChunkDto] = []
    seen_chunk_uuids: set[str] = set()
    top_k = max(1, COMMERCIAL_AREA_TOP_K)

    try:
        for query in search_queries:
            log.debug(f"[툴][search_commercial_area] BOS 요청 ▶ query={query!r} topK={top_k}")
            rows = _search_chunks(query, top_k, sigungu_code)
            log.debug(f"[툴][search_commercial_area] BOS 응답 ◀ {len(rows)}개 청크")
            for row in rows:
                normalized_row = _normalize_chunk_row(row, query)
                chunk_uuid = normalized_row.get("chunk_uuid")
                if chunk_uuid in seen_chunk_uuids:
                    continue
                seen_chunk_uuids.add(chunk_uuid)
                chunks.append(SearchCommercialAreaChunkDto.model_validate(normalized_row))
    except httpx.TimeoutException as exc:
        log.error(f"[툴][search_commercial_area] BOS 타임아웃 ({COMMERCIAL_AREA_TIMEOUT_SECONDS}s) | URL={BOS_SERVER_BASE_URL} | {exc}")
        return SearchCommercialAreaResultDto(
            error="상권 분석 조회 타임아웃",
            detail=str(exc),
            sigungu_code=sigungu_code,
            base_url=BOS_SERVER_BASE_URL,
        )
    except httpx.ConnectError as exc:
        log.error(f"[툴][search_commercial_area] BOS 연결 실패 | URL={BOS_SERVER_BASE_URL} | {exc}")
        return SearchCommercialAreaResultDto(
            error="BOS 서버 연결 실패 (URL 또는 서버 상태 확인)",
            detail=str(exc),
            sigungu_code=sigungu_code,
            base_url=BOS_SERVER_BASE_URL,
        )
    except httpx.HTTPStatusError as exc:
        log.error(f"[툴][search_commercial_area] BOS HTTP 오류 status={exc.response.status_code} | body={exc.response.text[:300]}")
        return SearchCommercialAreaResultDto(
            error="상권 분석 BOS 오류",
            detail=str(exc),
            status=exc.response.status_code,
            sigungu_code=sigungu_code,
        )
    except httpx.HTTPError as exc:
        log.error(f"[툴][search_commercial_area] BOS 요청 실패 | {exc}")
        return SearchCommercialAreaResultDto(
            error="상권 분석 조회 실패",
            detail=str(exc),
            sigungu_code=sigungu_code,
            base_url=BOS_SERVER_BASE_URL,
        )

    log.info(f"[툴][search_commercial_area] 완료 ▶ 총 {len(chunks)}개 청크")
    district = None
    if chunks:
        first_chunk = chunks[0]
        district = getattr(first_chunk, "district", None)
        if district is None and hasattr(first_chunk, "model_dump"):
            district = first_chunk.model_dump(mode="json", exclude_none=True).get("district")
    return SearchCommercialAreaResultDto(
        sigungu_code=sigungu_code,
        district=district,
        queries=search_queries,
        count=len(chunks),
        chunks=chunks,
    )
