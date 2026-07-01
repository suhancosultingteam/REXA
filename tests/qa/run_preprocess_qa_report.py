from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import json

from rexa.models.preprocess import preprocess_with_metrics
from tests.qa.extract_qa_questions import QAQuestion, load_questions


WORKBOOK_PATH = Path("260512_렉사응답_QA 테스트.xlsx")
OUTPUT_DIR = Path("tests/qa/reports")
REPORT_PATH = OUTPUT_DIR / "preprocess_qa_report.md"
JSON_PATH = OUTPUT_DIR / "preprocess_qa_report.json"


@dataclass
class PreprocessAuditResult:
    number: str
    expected_group: str
    category: str
    question: str
    expected_answer_type: str
    required_source: str
    predicted_group: str
    reason: str
    addresses: list[dict[str, Any]]
    error: str = ""


def _serialize_address(address: Any) -> dict[str, Any]:
    if hasattr(address, "model_dump"):
        return address.model_dump()
    return dict(address)


def run_audit(groups: dict[str, list[QAQuestion]]) -> list[PreprocessAuditResult]:
    results: list[PreprocessAuditResult] = []
    for expected_group, questions in groups.items():
        for item in questions:
            try:
                preprocessed, _ = preprocess_with_metrics(item.question)
                results.append(
                    PreprocessAuditResult(
                        number=item.number,
                        expected_group=expected_group,
                        category=item.category,
                        question=item.question,
                        expected_answer_type=item.expected_answer_type,
                        required_source=item.required_source,
                        predicted_group=preprocessed.query_type,
                        reason=preprocessed.reason,
                        addresses=[_serialize_address(addr) for addr in preprocessed.addresses],
                    )
                )
            except Exception as exc:
                results.append(
                    PreprocessAuditResult(
                        number=item.number,
                        expected_group=expected_group,
                        category=item.category,
                        question=item.question,
                        expected_answer_type=item.expected_answer_type,
                        required_source=item.required_source,
                        predicted_group="ERROR",
                        reason="",
                        addresses=[],
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
    return results


def _summary_rows(results: list[PreprocessAuditResult]) -> list[str]:
    header = "| 기대 | 총개수 | 일치 | 불일치 | 오류 |"
    divider = "| --- | ---: | ---: | ---: | ---: |"
    rows = [header, divider]
    for group in ("A", "B", "C", "D"):
        subset = [item for item in results if item.expected_group == group]
        matched = sum(1 for item in subset if item.predicted_group == group)
        errors = sum(1 for item in subset if item.predicted_group == "ERROR")
        mismatched = len(subset) - matched - errors
        rows.append(f"| {group} | {len(subset)} | {matched} | {mismatched} | {errors} |")
    return rows


def _format_result_block(item: PreprocessAuditResult) -> str:
    lines = [
        f"### [{item.number}] {item.category}",
        f"- 질문: {item.question}",
        f"- 기대 그룹: {item.expected_group}",
        f"- 실제 그룹: {item.predicted_group}",
        f"- 기대 답변 유형: {item.expected_answer_type}",
        f"- 필수 데이터 소스: {item.required_source}",
    ]
    if item.error:
        lines.append(f"- 오류: {item.error}")
        return "\n".join(lines)

    lines.append(f"- 판단 이유: {item.reason or '(없음)'}")
    if item.addresses:
        lines.append("- 추출 주소/키워드:")
        for address in item.addresses:
            keyword = address.get("keyword") or address.get("origin") or ""
            fullname = address.get("fullname") or ""
            lines.append(f"  - {keyword} -> {fullname}")
    else:
        lines.append("- 추출 주소/키워드: 없음")
    return "\n".join(lines)


def build_report(results: list[PreprocessAuditResult]) -> str:
    expected_a = [item for item in results if item.expected_group == "A"]
    a_matched = [item for item in expected_a if item.predicted_group == "A"]
    a_mismatched = [item for item in expected_a if item.predicted_group not in {"A"}]

    lines = [
        "# Preprocess QA Report",
        "",
        f"- 생성 시각: {datetime.now().isoformat(timespec='seconds')}",
        f"- 대상 파일: `{WORKBOOK_PATH}`",
        f"- 총 질문 수: {len(results)}",
        "",
        "## 전체 요약",
        "",
        *_summary_rows(results),
        "",
        "## A 기대 질문 중 A로 판단된 항목",
        "",
        f"- 개수: {len(a_matched)}",
        "",
    ]
    if a_matched:
        for item in a_matched:
            lines.append(_format_result_block(item))
            lines.append("")
    else:
        lines.append("없음")
        lines.append("")

    lines.extend(
        [
            "## A 기대 질문 중 A가 아닌 것으로 판단된 항목",
            "",
            f"- 개수: {len(a_mismatched)}",
            "",
        ]
    )
    if a_mismatched:
        for item in a_mismatched:
            lines.append(_format_result_block(item))
            lines.append("")
    else:
        lines.append("없음")
        lines.append("")

    lines.extend(
        [
            "## 전체 상세 결과",
            "",
        ]
    )
    for group in ("A", "B", "C", "D"):
        lines.append(f"## 기대 {group}")
        lines.append("")
        subset = [item for item in results if item.expected_group == group]
        for item in subset:
            lines.append(_format_result_block(item))
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_outputs(results: list[PreprocessAuditResult]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(results), encoding="utf-8")
    JSON_PATH.write_text(
        json.dumps([item.__dict__ for item in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    groups = load_questions(WORKBOOK_PATH)
    results = run_audit(groups)
    write_outputs(results)
    print(f"report -> {REPORT_PATH}")
    print(f"json -> {JSON_PATH}")


if __name__ == "__main__":
    main()
