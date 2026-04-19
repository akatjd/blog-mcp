"""YAML field 스펙을 Pydantic 모델로 변환하여 info 입력을 검증한다.

각 카테고리 YAML의 `fields:` 항목을 읽어
required/optional, type, min/max 제약을 가진 모델을 동적으로 생성한다.
"""
from typing import Any
from pydantic import BaseModel, Field, ValidationError, create_model

from tools import template_loader

_TYPE_MAP: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
}


def _build_model(category: str) -> type[BaseModel]:
    fields_def: dict[str, Any] = {}
    for field in template_loader.get_fields(category):
        py_type = _TYPE_MAP.get(field.get("type", "str"), str)
        required = field.get("required", False)

        constraints: dict[str, Any] = {"description": field.get("label", field["name"])}
        if "min" in field:
            constraints["ge"] = field["min"]
        if "max" in field:
            constraints["le"] = field["max"]

        if required:
            fields_def[field["name"]] = (py_type, Field(..., **constraints))
        else:
            fields_def[field["name"]] = (py_type | None, Field(None, **constraints))

    return create_model(f"{category.capitalize()}Info", **fields_def)


_MODELS: dict[str, type[BaseModel]] = {
    name: _build_model(name) for name in template_loader.get_categories()
}


def validate(category: str, info: dict) -> tuple[dict | None, str | None]:
    """info를 검증한다. (validated_dict, error_message) 중 하나만 반환."""
    model = _MODELS.get(category)
    if not model:
        return None, f"알 수 없는 카테고리: {category}"

    try:
        validated = model(**info)
    except ValidationError as e:
        return None, _format_error(category, e)

    # exclude_none=False — None도 그대로 통과 (템플릿이 빈 문자열로 처리)
    return validated.model_dump(), None


def _format_error(category: str, e: ValidationError) -> str:
    lines = [f"❌ {category} 입력 검증 실패:"]
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"])
        msg = err["msg"]
        lines.append(f"  - {loc}: {msg}")
    return "\n".join(lines)
