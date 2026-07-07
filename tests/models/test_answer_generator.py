from rexa.models.answer_v2.generator import _has_non_seoul_address, _needs_seoul_only_notice


def test_has_non_seoul_address_detects_gyeonggi_sigungu_code():
    retrieval_result = {
        "query_type": "A",
        "addresses": [{"sigungu_code": "41135"}],
    }

    assert _has_non_seoul_address(retrieval_result) is True


def test_needs_seoul_only_notice_for_non_seoul_address_without_retrieval():
    retrieval_result = {
        "query_type": "A",
        "addresses": [{"sigungu_code": "41135"}],
    }

    assert _needs_seoul_only_notice(retrieval_result, {}) is True


def test_needs_seoul_only_notice_is_false_for_seoul_address():
    retrieval_result = {
        "query_type": "A",
        "addresses": [{"sigungu_code": "11680"}],
    }

    assert _needs_seoul_only_notice(retrieval_result, {"search_commercial_area": [{}]}) is False
