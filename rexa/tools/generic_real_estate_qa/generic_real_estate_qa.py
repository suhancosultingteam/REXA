from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from rexa.infra.logger import setup_logger
from rexa.infra.llm_failover import build_chat_model, run_with_failover
from rexa.tools.generic_real_estate_qa.generic_real_estate_qa_input_dto import GenericRealEstateQAInputDto
from rexa.tools.generic_real_estate_qa.generic_real_estate_qa_result_dto import GenericRealEstateQAResultDto

load_dotenv()

log = setup_logger()

_SYSTEM_PROMPT = """당신은 일반적인 부동산 개념을 설명하는 도우미입니다.

역할:
- 조회 데이터나 RAG 없이 답할 수 있는 일반 부동산 질문에 교육용으로 답합니다.
- 개념 설명, 용어 정의, 일반적 해석, 초보자용 가이드에 집중합니다.

반드시 지킬 규칙:
- 최신 시세, 특정 지역의 현재 규제, 세율, 법률 해석, 계약서 조항 해석, 개인별 투자 판단, 대출 가능 여부처럼 민감하거나 최신성이 중요한 내용은 단정하지 마세요.
- 그런 질문이면 일반 원칙만 짧게 설명하고, '최신 규정과 개별 사실관계 확인이 필요합니다.'라고 적으세요.
- 의료, 법률, 세무, 투자 자문처럼 보일 수 있는 표현은 피하고 교육용 일반 정보로만 답하세요.
- 과장하지 말고, 확실하지 않은 내용은 보수적으로 표현하세요.
- 답변은 한국어로, 짧은 결론부터 시작하고 이해하기 쉽게 설명하세요.
- 마크다운 문법 없이 일반 텍스트만 사용하세요.
"""


@tool(args_schema=GenericRealEstateQAInputDto)
def generic_real_estate_qa(question: str) -> GenericRealEstateQAResultDto:
    """조회 없이 답할 수 있는 일반 부동산 개념 질문에 답합니다.

    사용 시점:
    - 전세와 월세 차이
    - cap rate 뜻
    - 공실률 의미
    - 상가 투자 기본 지표

    피해야 하는 질문:
    - 최신 규제/세율/법률 판단
    - 계약서 조항 해석
    - 특정 개인의 투자/대출 적합성 판단

    반환:
    - `question`, `answer`, `source`
    """
    normalized_question = (question or "").strip()
    log.info(f"[툴][generic_real_estate_qa] 시작 ▶ question={normalized_question!r}")

    if not normalized_question:
        return GenericRealEstateQAResultDto(error="일반 부동산 질문이 비어 있습니다.")

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=normalized_question),
    ]

    try:
        response = run_with_failover(
            "generic_real_estate_qa",
            log,
            primary_call=lambda: build_chat_model("claude", "fast", temperature=0).invoke(messages),
            fallback_call=lambda: build_chat_model("openai", "fast", temperature=0).invoke(messages),
        )
    except Exception as exc:
        log.error(f"[툴][generic_real_estate_qa] LLM 호출 실패 | {exc}")
        return GenericRealEstateQAResultDto(error="일반 부동산 질문 답변 생성 실패", detail=str(exc))

    answer = (response.content or "").strip()
    log.info(f"[툴][generic_real_estate_qa] 완료 ◀ 답변 {len(answer)}자")
    return GenericRealEstateQAResultDto(
        question=normalized_question,
        answer=answer,
        source="llm_general_knowledge",
    )
