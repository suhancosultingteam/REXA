from langchain.tools import tool
import os

from rexa.infra.logger import setup_logger
from rexa.tools._utils import KAKAO_HTTP_TIMEOUT_SECONDS, lookup_address
from rexa.tools.search_by_address.search_by_address_input_dto import SearchByAddressInputDto
from rexa.tools.search_by_address.search_by_address_result_dto import SearchByAddressResultDto

log = setup_logger()
KAKAO_KEY = os.getenv("KAKAO_REST_API_KEY")


@tool(args_schema=SearchByAddressInputDto)
def search_by_address(address: str) -> SearchByAddressResultDto:
    """주소 문자열로 좌표와 행정구역 정보를 검색합니다.

    사용 시점:
    - 지번 주소, 도로명 주소, 행정동/법정동 이름이 직접 주어진 경우
    - 고유명사 장소명이 아니라 주소 형식이나 동 이름을 처리할 때

    파라미터:
    - `address`: 주소 또는 동 이름 문자열

    반환:
    - 단건 매칭 시 주소, 좌표, sigungu_name/sigungu_code, bjdong_name/bjdong_code, bun, ji를 포함한 객체
    - 다건 매칭 시 `candidates` 배열
    - 실패 시 `error`
    """
    log.debug(
        f"[툴][search_by_address] 시작 ▶ "
        f"address={address!r} | KAKAO_KEY={'설정됨' if KAKAO_KEY else '없음(❌)'} | timeout={KAKAO_HTTP_TIMEOUT_SECONDS}s"
    )

    if not KAKAO_KEY:
        log.error("[툴][search_by_address] KAKAO_REST_API_KEY 환경변수 없음")
        return SearchByAddressResultDto(error="KAKAO_REST_API_KEY 미설정")

    try:
        payload = lookup_address(address, address)
        result = SearchByAddressResultDto.model_validate(payload)
    except Exception as exc:
        log.exception(f"[툴][search_by_address] 오류 ▶ address={address!r} | {exc}")
        return SearchByAddressResultDto(error=f"주소 조회 실패: {exc}")

    dump = result.model_dump(mode="json", exclude_none=True)
    if result.error:
        log.error(f"[툴][search_by_address] 실패 ▶ {dump}")
    else:
        log.debug(f"[툴][search_by_address] 완료 ▶ {dump}")
    return result
