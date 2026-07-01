from rexa.models.commercial_area_alias import match_commercial_area_aliases
import rexa.models.commercial_area_alias as commercial_area_alias


def test_match_commercial_area_aliases_returns_canonical_with_sigungu_code(monkeypatch):
    monkeypatch.setattr(commercial_area_alias, "lookup_sigungu_code", lambda name: "11680")

    matched = match_commercial_area_aliases("가로수길 근처 카페 상권 분석해줘")

    assert len(matched) == 1
    assert matched[0].keyword == "가로수길"
    assert matched[0].origin == "가로수길"
    assert matched[0].sigungu_name == "강남구"
    assert matched[0].sigungu_code == "11680"


def test_match_commercial_area_aliases_matches_typo_variant(monkeypatch):
    monkeypatch.setattr(commercial_area_alias, "lookup_sigungu_code", lambda name: "11680")

    matched = match_commercial_area_aliases("가르수길 맛집 추천해줘")

    assert len(matched) == 1
    assert matched[0].keyword == "가로수길"
    assert matched[0].origin == "가르수길"


def test_match_commercial_area_aliases_returns_empty_when_no_alias_found(monkeypatch):
    monkeypatch.setattr(commercial_area_alias, "lookup_sigungu_code", lambda name: "11680")

    assert match_commercial_area_aliases("강남역 전세 시세 알려줘") != []
    assert match_commercial_area_aliases("이건 부동산과 무관한 질문입니다") == []
