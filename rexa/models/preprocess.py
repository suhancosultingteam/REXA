import time
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import AliasChoices, BaseModel, Field

from rexa.infra.chat_logging import LayerMetrics, extract_token_usage
from rexa.infra.llm_failover import invoke_structured_with_failover
from rexa.infra.logger import setup_logger, log_llm_text
from rexa.models.commercial_area_alias import CommercialAreaAlias, match_commercial_area_aliases
from rexa.prompts import PREPROCESS_SYSTEM_PROMPT
from rexa.tools import search_by_address, search_by_keyword

QueryType = Literal["A", "B", "C", "D"]

load_dotenv()

log = setup_logger()


class AddressObject(BaseModel):
    keyword: str
    origin: str
    fullname: str
    sigungu_name: str = Field(validation_alias=AliasChoices("sigungu_name", "gu"))
    sigungu_code: str = Field(default="", validation_alias=AliasChoices("sigungu_code", "gu_code"))
    bjdong_name: str = Field(validation_alias=AliasChoices("bjdong_name", "dong"))
    bjdong_code: str = Field(default="", validation_alias=AliasChoices("bjdong_code", "dong_code"))
    bun: str = ""
    ji: str = ""
    lat: float
    lng: float


class PreprocessResult(BaseModel):
    origin: str = Field(description="사용자 원본 입력")
    query_type: QueryType = Field(description="질문 분류. A/B/C/D 중 하나")
    reason: str = Field(
        default="",
        description="query_type 판단 이유"
    )
    addresses: list[AddressObject] = Field(default_factory=list, description="검색된 장소/주소")
    commercial_areas: list[CommercialAreaAlias] = Field(default_factory=list, description="매칭된 상권 alias")

    @property
    def route(self) -> Literal["in_domain", "fallback"]:
        return "in_domain" if self.query_type in {"A", "C"} else "fallback"

    @property
    def decision_code(self) -> str:
        mapping = {
            "A": "ALLOW_DOMAIN",
            "B": "ALLOW_FALLBACK",
            "C": "LIMITED_GUIDE",
            "D": "REFUSE_POLICY",
        }
        return mapping[self.query_type]

    @property
    def response_mode(self) -> str:
        if self.query_type == "C":
            return "safe_brief"
        if self.query_type == "D":
            return "template_only"
        return "normal"

    @property
    def template_code(self) -> str:
        return "OUT_OF_SCOPE" if self.query_type == "D" else ""

    @property
    def risk_flags(self) -> list[str]:
        return ["judgment"] if self.query_type == "C" else []


class PreprocessCandidates(BaseModel):
    query_type: QueryType = Field(
        description=(
            "A: 주소·건물·지역·매물·상권 조회 중심 질문. 비교·정렬·순위·선별과 "
            "상권 비교, 업종 적합도, 매물 1차 검토, 적정가 참고, 투자 우선순위, 추천/점수화 같은 "
            "분석형 정식답변도 포함한다. "
            "B: generic_real_estate_qa 로 처리할 일반 부동산 개념·용어·원리 설명 질문. "
            "아파트·전세·월세·빌라·오피스텔·주택 같은 주거 일반 질문과, "
            "직접 조회 범위 밖이지만 일반 상식으로 설명 가능한 주거 시세 일반론·전세가율·제도 설명·투자 일반론을 포함한다. "
            "C: 조회는 가능해도 최종 답이 해석·평가·추천·가격판단·투자판단·권리판단처럼 책임이 큰 질문. "
            "특히 세무, 대출/LTV, 권리관계, 명도, 인허가, 위반건축물, 재건축/재개발 수익, 감정평가·KB시세가 여기에 해당한다. "
            "D: 부동산 범위 밖 질문. 우선순위는 D > C > A > B."
        )
    )

    reason: str = Field(
        default="",
        description=(
            "분류 이유를 짧게 적는다. "
            "예: '강남역 상권 분석처럼 특정 지역 조회가 중심이라 A', "
            "'월세 정의를 묻는 개념 질문이라 B', "
            "'가격 적정성 판단 요구라 C', "
            "'부동산과 무관해 D'."
        )
    )

    addresses: list[str] = Field(
        default_factory=list,
        description=(
            "주소 검색 툴로 바로 조회할 표현 목록. "
            "지번 주소, 도로명 주소, 행정구, 행정동, 법정동 이름을 넣는다. "
            "예: '세종로 1-1', '강남대로 123', '강남구', '역삼동'. "
            "건물명·역명 같은 고유명사는 keywords로 보낸다."
        )
    )
    keywords: list[str] = Field(
        default_factory=list,
        description=(
            "키워드 검색이 필요한 고유명사 장소 목록. "
            "건물명, 역명, 랜드마크, 상호명처럼 이름으로 알려진 장소를 넣는다. "
            "예: '경복궁', '강남역', '코엑스', '롯데타워'. "
            "업종명이나 일반명사(카페, 식당, 아파트, 상가)는 넣지 않는다."
        )
    )

def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _normalize_lookup_result(result: dict, fallback_origin: str) -> AddressObject | None:
    if not isinstance(result, dict) or "error" in result:
        return None

    payload = dict(result)
    if not payload.get("origin"):
        payload["origin"] = fallback_origin
    return AddressObject.model_validate(payload)


def _normalize_lookup_results(result: dict, fallback_origin: str) -> list[AddressObject]:
    if not isinstance(result, dict) or "error" in result:
        return []

    candidates = result.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        normalized = _normalize_lookup_result(result, fallback_origin)
        return [normalized] if normalized is not None else []

    seen: set[tuple[str, str, str, str]] = set()
    for candidate in candidates:
        normalized = _normalize_lookup_result(candidate, fallback_origin)
        if normalized is None:
            continue
        key = (
            normalized.sigungu_code,
            normalized.bjdong_code,
            normalized.bun,
            normalized.ji,
        )
        if key in seen:
            continue
        seen.add(key)
        return [normalized]
    return []


def preprocess_with_metrics(
    user_input: str,
    history: list[dict] | None = None,
) -> tuple[PreprocessResult, LayerMetrics]:
    started_at = time.perf_counter()
    log.info(f"[전처리] 시작 ▶ 입력: {user_input!r}")
    messages: list = [SystemMessage(content=PREPROCESS_SYSTEM_PROMPT)]
    for msg in (history or []):
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_input))
    log.info(f"[전처리] message : {messages}")
    log_llm_text(log, "[전처리]", " input ", user_input)
    extracted_payload, provider, model_name = invoke_structured_with_failover(
        "preprocess_structured",
        log,
        PreprocessCandidates,
        messages,
        profile="fast",
    )
    raw_message = extracted_payload
    extracted = extracted_payload
    if isinstance(extracted_payload, dict) and "parsed" in extracted_payload:
        extracted = extracted_payload.get("parsed")
        raw_message = extracted_payload.get("raw")
    if extracted is None:
        raise RuntimeError("preprocess structured output parsing failed")
    log_llm_text(log, "[전처리]", " output ", extracted.model_dump_json(indent=2))

    address_queries = _dedupe_preserve_order(extracted.addresses)
    keyword_queries = _dedupe_preserve_order(extracted.keywords)
    log.info(f"[전처리] 추출 완료 ▶ addresses={len(address_queries)} keywords={len(keyword_queries)}")

    def _resolve_address(address: str) -> dict:
        log.info(f"[전처리] 주소 조회 ▶ {address!r}")
        result_dto = search_by_address.invoke({"address": address})
        result = result_dto.model_dump(mode="json", exclude_none=True)
        if result.get("error"):
            log.warning(f"[전처리] 주소 조회 실패 ▶ address={address!r} | error={result['error']}")
        return result

    def _resolve_keyword(keyword: str) -> dict:
        log.info(f"[전처리] 키워드 조회 ▶ {keyword!r}")
        result_dto = search_by_keyword.invoke({"keyword": keyword})
        result = result_dto.model_dump(mode="json", exclude_none=True)
        if result.get("error"):
            log.warning(f"[전처리] 키워드 조회 실패 ▶ keyword={keyword!r} | error={result['error']}")
        return result

    resolved_addresses: list[AddressObject] = []
    if address_queries or keyword_queries:
        with ThreadPoolExecutor(max_workers=max(1, len(address_queries) + len(keyword_queries))) as pool:
            address_futures = [(address, pool.submit(_resolve_address, address)) for address in address_queries]
            keyword_futures = [(keyword, pool.submit(_resolve_keyword, keyword)) for keyword in keyword_queries]

        for address, future in address_futures:
            resolved_addresses.extend(_normalize_lookup_results(future.result(), address))
        for keyword, future in keyword_futures:
            resolved_addresses.extend(_normalize_lookup_results(future.result(), keyword))

    seen_alias_keys: set[tuple[str, str]] = set()
    commercial_areas: list[CommercialAreaAlias] = []
    search_terms = address_queries + keyword_queries
    log.info(f"[전처리][상권alias] 매칭 시작 ▶ 검색 대상 terms={search_terms}")
    for term in search_terms:
        matched = match_commercial_area_aliases(term)
        log.debug(f"[전처리][상권alias] term={term!r} → 매칭 결과 {len(matched)}건: {[a.model_dump() for a in matched]}")
        for alias in matched:
            key = (alias.keyword, alias.sigungu_code)
            if key in seen_alias_keys:
                log.debug(f"[전처리][상권alias] 중복 스킵 ▶ key={key}")
                continue
            seen_alias_keys.add(key)
            commercial_areas.append(alias)
    if commercial_areas:
        log.info(f"[전처리][상권alias] 매칭 완료 ▶ {len(commercial_areas)}건: {[c.model_dump() for c in commercial_areas]}")
    else:
        log.warning(f"[전처리][상권alias] 매칭 결과 없음 ▶ terms={search_terms}")

    result = PreprocessResult(
        origin=user_input,
        query_type=extracted.query_type,
        reason=extracted.reason,
        addresses=resolved_addresses,
        commercial_areas=commercial_areas,
    )

    log.info(f"[전처리] 완료 ◀ 결과\n{result.model_dump_json(indent=2)}")

    metrics = LayerMetrics(
        provider=provider,
        model_name=model_name,
        latency_ms=int((time.perf_counter() - started_at) * 1000),
        tokens=extract_token_usage(raw_message),
    )
    return result, metrics


def preprocess(user_input: str, history: list[dict] | None = None) -> PreprocessResult:
    result, _ = preprocess_with_metrics(user_input, history=history)
    return result
