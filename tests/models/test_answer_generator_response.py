from rexa.models.answer_v2.generator import generate_answer_with_metrics


def test_non_seoul_without_successful_retrieval_returns_seoul_only_message():
    retrieval_result = {
        "origin": "경안천로 159 건물 조회해줘",
        "query_type": "A",
        "addresses": [{"sigungu_code": "41461"}],
        "retrieval": {
            "get_building_registry": [
                {"error": "조회 결과 없음"},
            ]
        },
    }

    answer, _ = generate_answer_with_metrics(retrieval_result)

    assert "렉사는 현재 서울 지역 분석만 지원합니다." in answer
    assert "서울 외 지역은 주소를 더 구체적으로 보내주셔도 현재는 조회가 어렵습니다." in answer
    assert "용인시 처인구" not in answer
