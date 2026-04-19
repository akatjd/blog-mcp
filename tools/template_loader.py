"""YAML 기반 카테고리 템플릿 로더.

`templates/categories/*.yaml`을 스캔하여 카테고리를 등록한다.
각 YAML은 fields(입력 스펙), computed_fields(파생 변수), prompt(템플릿)를 정의한다.
"""
import yaml
from pathlib import Path

from tools.style_analyzer import load_style_profile, build_style_instruction

CATEGORIES_DIR = Path(__file__).parent.parent / "templates" / "categories"


class _SafeDict(dict):
    """포맷 시 누락된 키는 빈 문자열로 대체한다."""

    def __missing__(self, key):
        return ""


def _load_all() -> dict[str, dict]:
    templates = {}
    for path in sorted(CATEGORIES_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        name = data.get("name") or path.stem
        templates[name] = data
    return templates


_TEMPLATES = _load_all()


def get_categories() -> list[str]:
    return list(_TEMPLATES.keys())


def get_template(category: str) -> dict:
    if category not in _TEMPLATES:
        raise ValueError(
            f"알 수 없는 카테고리: {category}. 사용 가능: {get_categories()}"
        )
    return _TEMPLATES[category]


def get_fields(category: str) -> list[dict]:
    return get_template(category).get("fields", [])


def build_prompt(category: str, info: dict) -> str:
    """info를 받아 카테고리 템플릿에 채워 넣은 최종 프롬프트를 반환한다."""
    tpl = get_template(category)

    values = _SafeDict()
    for field in tpl.get("fields", []):
        v = info.get(field["name"])
        values[field["name"]] = "" if v is None else v

    # 공통 파생 필드
    values["extra_line"] = (
        f"- 추가 메모: {info['extra']}" if info.get("extra") else ""
    )
    profile = load_style_profile()
    values["style_section"] = (
        f"\n{build_style_instruction(profile)}\n" if profile else ""
    )

    # 카테고리별 파생 필드 (YAML 선언)
    for derived in tpl.get("computed_fields", []) or []:
        condition_field = derived.get("if_field")
        condition_value = info.get(condition_field) if condition_field else True
        if condition_value:
            values[derived["name"]] = derived.get("template", "").format_map(values)
        else:
            values[derived["name"]] = derived.get("default", "")

    return tpl["prompt"].format_map(values)
