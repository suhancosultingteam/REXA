from rexa.prompts import ROUTER_SYSTEM_PROMPT
from rexa.models.router_v3 import _ROUTER_V3_SYSTEM_PROMPT


def test_router_system_prompt_prefers_rent_for_office_queries():
    assert "오피스 찾아줘" in ROUTER_SYSTEM_PROMPT
    assert "사무실 구해줘" in ROUTER_SYSTEM_PROMPT
    assert "get_suhan_rent_property" in ROUTER_SYSTEM_PROMPT
    assert "오피스/사무실 계열은 `get_suhan_rent_property`를 우선 사용" in ROUTER_SYSTEM_PROMPT


def test_router_v3_system_prompt_prefers_rent_for_office_queries():
    assert "오피스 찾아줘" in _ROUTER_V3_SYSTEM_PROMPT
    assert "사무실 구해줘" in _ROUTER_V3_SYSTEM_PROMPT
    assert "get_suhan_rent_property" in _ROUTER_V3_SYSTEM_PROMPT
    assert "오피스/사무실 계열은 get_suhan_rent_property 를 우선 사용" in _ROUTER_V3_SYSTEM_PROMPT
