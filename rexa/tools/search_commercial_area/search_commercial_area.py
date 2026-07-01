import os

import httpx
from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._utils import error_result
from rexa.tools.search_commercial_area.search_commercial_area_chunk_dto import SearchCommercialAreaChunkDto
from rexa.tools.search_commercial_area.search_commercial_area_input_dto import SearchCommercialAreaInputDto
from rexa.tools.search_commercial_area.search_commercial_area_result_dto import SearchCommercialAreaResultDto

BOS_SERVER_BASE_URL = os.getenv("BOS_SERVER_BASE_URL", "http://localhost:10000").rstrip("/")
COMMERCIAL_AREA_TOP_K = int(os.getenv("COMMERCIAL_AREA_TOP_K", "5"))
COMMERCIAL_AREA_TIMEOUT_SECONDS = float(os.getenv("COMMERCIAL_AREA_TIMEOUT_SECONDS", "20"))
log = setup_logger()


def _build_search_queries(queries: list[str]) -> list[str]:
    return [q.strip() for q in queries if q.strip()]


def _search_chunks(query: str, top_k: int, sigungu_code: str) -> list[dict]:
    response = httpx.get(
        f"{BOS_SERVER_BASE_URL}/commercial-area-reports/chunks/search",
        params={"query": query, "topK": top_k, "sigunguCode": sigungu_code},
        timeout=COMMERCIAL_AREA_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("rows", [])


@tool(args_schema=SearchCommercialAreaInputDto)
def search_commercial_area(sigungu_code: str, queries: list[str]) -> SearchCommercialAreaResultDto:
    """구 단위 상권 분석 보고서를 벡터 검색으로 조회합니다.

    사용 시점:
    - 상권, 유동인구, 업종 분포, 생존률, 입지 평가 질문
    - 주소가 구 단위여도 사용할 수 있습니다

    파라미터:
    - `sigungu_code`: 조회 대상 구의 5자리 시군구 코드
    - `queries`: 보고서 검색용 자연어 쿼리 배열

    반환:
    - `sigungu_code`: 실제 조회한 구 코드
    - `queries`: 정제된 검색 쿼리
    - `count`: 매칭된 청크 수
    - `chunks`: 검색된 상권 보고서 청크 목록
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
                chunk_uuid = row.get("chunkUuid") or row.get("chunk_uuid") or row.get("id")
                if chunk_uuid in seen_chunk_uuids:
                    continue
                seen_chunk_uuids.add(chunk_uuid)
                row["matched_query"] = query
                chunks.append(SearchCommercialAreaChunkDto.model_validate(row))
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
    return SearchCommercialAreaResultDto(
        sigungu_code=sigungu_code,
        queries=search_queries,
        count=len(chunks),
        chunks=chunks,
    )
