from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


WORKBOOK_PATH = Path("260512_렉사응답_QA 테스트.xlsx")
OUTPUT_DIR = Path("tests/qa/questions")
SHEET_BY_GROUP = {
    "A": "xl/worksheets/sheet2.xml",
    "B": "xl/worksheets/sheet4.xml",
    "C": "xl/worksheets/sheet5.xml",
    "D": "xl/worksheets/sheet6.xml",
}
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


@dataclass
class QAQuestion:
    number: str
    group: str
    category: str
    question: str
    expected_answer_type: str
    required_source: str


def _load_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("a:si", NS):
        text = "".join(node.text or "" for node in item.iterfind(".//a:t", NS))
        values.append(text)
    return values


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value_node = cell.find("a:v", NS)
    raw = "" if value_node is None or value_node.text is None else value_node.text
    if cell_type == "s" and raw:
        return shared_strings[int(raw)]
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iterfind(".//a:t", NS))
    return raw


def load_questions(workbook_path: Path) -> dict[str, list[QAQuestion]]:
    groups: dict[str, list[QAQuestion]] = {group: [] for group in SHEET_BY_GROUP}
    with zipfile.ZipFile(workbook_path) as archive:
        shared_strings = _load_shared_strings(archive)
        for group, sheet_path in SHEET_BY_GROUP.items():
            sheet = ET.fromstring(archive.read(sheet_path))
            rows = sheet.find("a:sheetData", NS).findall("a:row", NS)
            for row in rows[1:]:
                cells = [_cell_value(cell, shared_strings) for cell in row.findall("a:c", NS)]
                if len(cells) < 6:
                    continue
                question = cells[3].strip()
                if not question:
                    continue
                groups[group].append(
                    QAQuestion(
                        number=cells[0].strip(),
                        group=cells[1].strip() or group,
                        category=cells[2].strip(),
                        question=question,
                        expected_answer_type=cells[4].strip(),
                        required_source=cells[5].strip(),
                    )
                )
    return groups


def write_group_file(group: str, questions: list[QAQuestion], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{group}.txt"
    lines = [
        f"[{item.number}] {item.question} | 카테고리={item.category} | 기대유형={item.expected_answer_type}"
        for item in questions
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    groups = load_questions(WORKBOOK_PATH)
    for group, questions in groups.items():
        output_path = write_group_file(group, questions, OUTPUT_DIR)
        print(f"{group}: {len(questions)} questions -> {output_path}")


if __name__ == "__main__":
    main()
