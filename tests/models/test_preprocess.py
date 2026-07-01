from rexa.models.commercial_area_alias import CommercialAreaAlias
from rexa.models.preprocess import PreprocessResult, _dedupe_preserve_order, _normalize_lookup_results


def test_dedupe_preserve_order_trims_and_keeps_first_seen_value():
    assert _dedupe_preserve_order([" 강남구 ", "역삼동", "강남구", "", " 역삼동 "]) == [
        "강남구",
        "역삼동",
    ]


def test_normalize_lookup_results_returns_single_normalized_candidate():
    result = {
        "candidates": [
            {
                "keyword": "경복궁",
                "origin": "세종로 1-1",
                "fullname": "서울 종로구 세종로 1-1",
                "sigungu_name": "종로구",
                "sigungu_code": "11110",
                "bjdong_name": "세종로",
                "bjdong_code": "1111010100",
                "bun": "0001",
                "ji": "0001",
                "lat": 37.579617,
                "lng": 126.977041,
            }
        ]
    }

    normalized = _normalize_lookup_results(result, "경복궁")

    assert len(normalized) == 1
    assert normalized[0].keyword == "경복궁"
    assert normalized[0].fullname == "서울 종로구 세종로 1-1"


def test_normalize_lookup_results_ignores_error_payload():
    assert _normalize_lookup_results({"error": "not found"}, "경복궁") == []


def test_preprocess_result_commercial_areas_defaults_to_empty_list():
    result = PreprocessResult(origin="강남역 맛집 추천해줘", query_type="A")

    assert result.commercial_areas == []


def test_preprocess_result_accepts_commercial_areas():
    alias = CommercialAreaAlias(
        keyword="가로수길", origin="가로수길", sigungu_name="강남구", sigungu_code="11680"
    )

    result = PreprocessResult(
        origin="가로수길 상권 분석해줘", query_type="A", commercial_areas=[alias]
    )

    assert result.commercial_areas == [alias]
