from rexa.tools.search_commercial_area.search_commercial_area import _build_search_queries, _normalize_chunk_row


def test_build_search_queries_drops_generic_duplicates_when_specific_queries_exist():
    queries = _build_search_queries([
        "강남구 상권",
        "강남구 상권분석",
        "강남구 유동인구",
        "강남구 업종 분포",
        "강남구 생존률",
    ])

    assert queries == [
        "강남구 유동인구",
        "강남구 업종 분포",
        "강남구 생존률",
    ]


def test_normalize_chunk_row_maps_text_score_and_district_aliases():
    row = {
        "chunkUuid": "abc",
        "chunkText": "강남역 상권은 유동이 강하다.",
        "searchScore": 0.91,
        "sigunguName": "강남구",
    }

    normalized = _normalize_chunk_row(row, "강남구 유동인구")

    assert normalized["chunk_uuid"] == "abc"
    assert normalized["text"] == "강남역 상권은 유동이 강하다."
    assert normalized["score"] == 0.91
    assert normalized["district"] == "강남구"
    assert normalized["matched_query"] == "강남구 유동인구"
