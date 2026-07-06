from rexa.prompts import ROUTER_SYSTEM_PROMPT


def test_router_system_prompt_prefers_rent_for_office_queries():
    assert "오피스 찾아줘" in ROUTER_SYSTEM_PROMPT
    assert "사무실 구해줘" in ROUTER_SYSTEM_PROMPT
    assert "get_suhan_rent_property" in ROUTER_SYSTEM_PROMPT
    assert "오피스/사무실 계열은 `get_suhan_rent_property`를 우선 사용" in ROUTER_SYSTEM_PROMPT


def test_router_system_prompt_keeps_router_v3_rules():
    assert "query_type을 반드시 참고하세요." in ROUTER_SYSTEM_PROMPT
    assert "D 타입이면 tool_calls 를 만들지 마세요." in ROUTER_SYSTEM_PROMPT
    assert "충분한 정보가 없어서 조회할 수 없는 툴은 호출하지 마세요." in ROUTER_SYSTEM_PROMPT
