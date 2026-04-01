"""공통 유틸리티 함수."""

from __future__ import annotations

import json


def ensure_list(val: list | str | None) -> list:
    """ARRAY 컬럼 값을 list로 보장한다. SQLite에서는 JSON 문자열로 올 수 있다."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def ensure_dict(val: dict | str | None) -> dict:
    """JSONB 컬럼 값을 dict로 보장한다."""
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}
