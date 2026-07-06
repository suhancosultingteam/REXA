from rexa.models.answer_v2.context_builder import _select_commercial_area_chunks
from rexa.tools.search_commercial_area.search_commercial_area import _build_search_queries


def test_build_search_queries_caps_at_three_unique_queries():
    queries = _build_search_queries([
        "강남역 카페 입지",
        "강남역 유동인구",
        "강남역 매출 전환",
        "강남역 카페 입지",
        "강남역 임대료",
    ])

    assert queries == [
        "강남역 카페 입지",
        "강남역 유동인구",
        "강남역 매출 전환",
    ]


def test_select_commercial_area_chunks_maximizes_query_coverage_first():
    chunks = [
        {"matched_query": "강남", "score": 0.99, "text": "강남-1"},
        {"matched_query": "강남", "score": 0.95, "text": "강남-2"},
        {"matched_query": "강동", "score": 0.94, "text": "강동-1"},
        {"matched_query": "강동", "score": 0.90, "text": "강동-2"},
        {"matched_query": "강서", "score": 0.89, "text": "강서-1"},
        {"matched_query": "강서", "score": 0.88, "text": "강서-2"},
    ]

    selected = _select_commercial_area_chunks(chunks, 4)

    assert [chunk["text"] for chunk in selected] == [
        "강남-1",
        "강동-1",
        "강서-1",
        "강남-2",
    ]


def test_select_commercial_area_chunks_sorts_within_each_query_by_score():
    chunks = [
        {"matched_query": "강남", "score": 0.80, "text": "강남-2"},
        {"matched_query": "강남", "score": 0.91, "text": "강남-1"},
        {"matched_query": "강동", "score": 0.70, "text": "강동-2"},
        {"matched_query": "강동", "score": 0.95, "text": "강동-1"},
    ]

    selected = _select_commercial_area_chunks(chunks, 4)

    assert [chunk["text"] for chunk in selected] == [
        "강남-1",
        "강동-1",
        "강남-2",
        "강동-2",
    ]
