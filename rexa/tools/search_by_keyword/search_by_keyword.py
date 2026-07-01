import os

import httpx
from dotenv import load_dotenv
from langchain.tools import tool

from rexa.infra.logger import setup_logger
from rexa.tools._utils import KAKAO_SEARCH_SIZE, lookup_addresses
from rexa.tools.search_by_keyword.search_by_keyword_input_dto import SearchByKeywordInputDto
from rexa.tools.search_by_keyword.search_by_keyword_result_dto import SearchByKeywordResultDto

load_dotenv()

KAKAO_KEY = os.getenv("KAKAO_REST_API_KEY")
log = setup_logger()


@tool(args_schema=SearchByKeywordInputDto)
def search_by_keyword(keyword: str) -> SearchByKeywordResultDto:
    """고유명사 장소명으로 주소와 좌표를 검색합니다.

    사용 시점:
    - 건물명, 지하철역, 랜드마크, 상호명처럼 이름으로 알려진 장소를 처리할 때
    - 지번/도로명 주소가 아니라 키워드 검색이 필요한 경우

    파라미터:
    - `keyword`: 장소명 또는 상호명

    반환:
    - 단건 매칭 시 주소, 좌표, sigungu_name/sigungu_code, bjdong_name/bjdong_code, bun, ji를 포함한 객체
    - 다건 매칭 시 `candidates` 배열
    - 실패 시 `error`
    """
    log.debug(f"[툴][search_by_keyword] 시작 ▶ keyword={keyword!r} | KAKAO_KEY={'설정됨' if KAKAO_KEY else '없음(❌)'}")

    if not KAKAO_KEY:
        log.error("[툴][search_by_keyword] KAKAO_REST_API_KEY 환경변수 없음")
        return SearchByKeywordResultDto(error="KAKAO_REST_API_KEY 미설정")

    try:
        res = httpx.get(
            "https://dapi.kakao.com/v2/local/search/keyword.json",
            headers={"Authorization": f"KakaoAK {KAKAO_KEY}"},
            params={"query": keyword, "size": KAKAO_SEARCH_SIZE},
            timeout=10,
        )
    except httpx.TimeoutException:
        log.error(f"[툴][search_by_keyword] Kakao API 타임아웃 | keyword={keyword!r}")
        return SearchByKeywordResultDto(error=f"{keyword} Kakao API 타임아웃")
    except httpx.HTTPError as exc:
        log.error(f"[툴][search_by_keyword] Kakao API 연결 실패 | {exc}")
        return SearchByKeywordResultDto(error=f"Kakao API 연결 실패: {exc}")

    log.debug(f"[툴][search_by_keyword] Kakao 응답 status={res.status_code} | body={res.text[:200]}")

    if res.status_code != 200:
        log.error(f"[툴][search_by_keyword] Kakao API 오류 status={res.status_code} | body={res.text[:300]}")
        return SearchByKeywordResultDto(error=f"Kakao API {res.status_code}: {res.text[:200]}")

    try:
        docs = res.json().get("documents", [])
    except Exception as exc:
        log.error(f"[툴][search_by_keyword] 응답 JSON 파싱 실패 | body={res.text[:300]} | {exc}")
        return SearchByKeywordResultDto(error=f"Kakao 응답 파싱 실패: {exc}")

    if not docs:
        log.warning(f"[툴][search_by_keyword] 결과 없음 | keyword={keyword!r}")
        return SearchByKeywordResultDto(error=f"{keyword}를 찾을 수 없음")

    address_names: list[str] = []
    seen: set[str] = set()
    for doc in docs:
        address_name = (doc.get("address_name") or "").strip()
        if not address_name or address_name in seen:
            continue
        seen.add(address_name)
        address_names.append(address_name)

    if not address_names:
        log.warning(f"[툴][search_by_keyword] 주소 필드 없음 | doc={docs[0]}")
        return SearchByKeywordResultDto(error=f"{keyword} 주소 없음")

    log.debug(f"[툴][search_by_keyword] 완료 ▶ address_names={address_names!r}")
    payload = lookup_addresses(keyword, address_names)
    return SearchByKeywordResultDto.model_validate(payload)
