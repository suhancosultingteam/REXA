import json
from pathlib import Path

from pydantic import BaseModel

from rexa.infra.logger import setup_logger
from rexa.tools._utils import lookup_sigungu_code

log = setup_logger()

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "commercial_area_aliases.json"


class CommercialAreaAlias(BaseModel):
    keyword: str
    origin: str
    sigungu_name: str
    sigungu_code: str = ""


def _load_entries() -> list[dict]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_ENTRIES = _load_entries()

# 긴 표현부터 매칭해서 짧은 표현이 더 구체적인 표현을 가리는 걸 방지
_TERM_INDEX: list[tuple[str, dict]] = sorted(
    ((term, entry) for entry in _ENTRIES for term in entry["terms"]),
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def match_commercial_area_aliases(text: str) -> list[CommercialAreaAlias]:
    if not text:
        log.debug("[상권alias] text 비어있음 → 스킵")
        return []

    norm_text = text.replace(" ", "")
    matched: dict[str, str] = {}
    for term, entry in _TERM_INDEX:
        alias_id = entry["alias_id"]
        if alias_id in matched:
            continue
        if term in text or term.replace(" ", "") in norm_text:
            matched[alias_id] = term
            log.debug(f"[상권alias] 히트 ▶ text={text!r} | term={term!r} | alias_id={alias_id}")

    if not matched:
        log.debug(f"[상권alias] 매칭 없음 ▶ text={text!r}")

    results: list[CommercialAreaAlias] = []
    for entry in _ENTRIES:
        alias_id = entry["alias_id"]
        if alias_id not in matched:
            continue
        for district in entry["districts"]:
            sigungu_code = lookup_sigungu_code(district)
            log.debug(f"[상권alias] alias 생성 ▶ canonical={entry['canonical']!r} district={district!r} sigungu_code={sigungu_code!r}")
            results.append(
                CommercialAreaAlias(
                    keyword=entry["canonical"],
                    origin=matched[alias_id],
                    sigungu_name=district,
                    sigungu_code=sigungu_code,
                )
            )
    return results
