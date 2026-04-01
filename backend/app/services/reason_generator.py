"""추천 이유 생성 모듈.

기획서 섹션 6.4 구현.
5축 가중 기여도 상위 2개 축을 선정하여 자연어 추천 이유를 생성한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PALETTES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "palettes"

DEFAULT_WEIGHTS: dict[str, float] = {
    "pcf": 0.25,
    "of": 0.20,
    "ch": 0.15,
    "pe": 0.15,
    "sf": 0.25,
}

TEMPLATES: dict[str, dict[str, str]] = {
    "pcf": {
        "high": "{tone_name} 핵심 컬러와 잘 어울려서 피부톤이 한층 밝아 보여요",
        "mid": "퍼스널컬러와 비교적 잘 어울리는 색상 구성이에요",
    },
    "of": {
        "high": "{tpo} 룩에 적합한 스타일링이에요",
        "mid": "다양한 상황에 무난하게 활용할 수 있는 스타일이에요",
    },
    "ch": {
        "high": "메인-서브-포인트 컬러가 균형 있게 조화를 이뤄요",
        "mid": "전체적으로 안정감 있는 색상 배합이에요",
    },
    "pe": {
        "high": "예산 범위 내에서 가성비 좋은 조합이에요",
        "mid": "가격 대비 만족스러운 구성이에요",
    },
    "sf": {
        "high": "스타일 조화가 뛰어난 코디예요",
        "mid": "전체적으로 무난한 스타일 구성이에요",
    },
}

_tone_names: dict[str, str] | None = None


def _load_tone_names() -> dict[str, str]:
    """팔레트 JSON에서 tone_id → tone_name_ko 매핑을 로드한다."""
    global _tone_names
    if _tone_names is not None:
        return _tone_names

    mapping: dict[str, str] = {}
    for palette_file in PALETTES_DIR.glob("*.json"):
        with open(palette_file, encoding="utf-8") as f:
            data = json.load(f)
        tone_id = data.get("tone_id")
        tone_name_ko = data.get("tone_name_ko")
        if tone_id and tone_name_ko:
            mapping[tone_id] = tone_name_ko

    _tone_names = mapping
    return _tone_names


TPO_NAMES_KO: dict[str, str] = {
    "commute": "출근",
    "office": "오피스",
    "weekend": "주말",
    "casual": "캐주얼",
    "daily": "데일리",
    "interview": "면접",
    "campus": "캠퍼스",
    "event": "행사",
    "party": "파티",
    "wedding": "하객",
    "workout": "운동",
    "date": "데이트",
    "travel": "여행",
}


def _select_top_axes(
    scores: dict[str, float],
    weights: dict[str, float] | None = None,
    n: int = 2,
) -> list[tuple[str, float, float]]:
    """가중 기여도 상위 n개 축을 반환한다.

    Returns:
        [(axis, raw_score, contribution), ...] 내림차순
    """
    w = weights or DEFAULT_WEIGHTS
    contributions: list[tuple[str, float, float]] = []

    for axis in DEFAULT_WEIGHTS:
        raw = scores.get(axis, 0.0)
        weight = w.get(axis, 0.0)
        contributions.append((axis, raw, raw * weight))

    contributions.sort(key=lambda x: x[2], reverse=True)
    return contributions[:n]


def _render_template(
    axis: str,
    raw_score: float,
    tone_name: str | None = None,
    tpo: str | None = None,
) -> str:
    """축과 점수에 따라 템플릿을 렌더링한다."""
    level = "high" if raw_score >= 75 else "mid"
    template = TEMPLATES[axis][level]

    if axis == "pcf" and level == "high":
        name = tone_name or "퍼스널컬러"
        return template.format(tone_name=name)

    if axis == "of" and level == "high":
        tpo_name = TPO_NAMES_KO.get(tpo, tpo) if tpo else "일상"
        return template.format(tpo=tpo_name)

    return template


def generate_reasons(
    scores: dict[str, float],
    user_tone_id: str | None = None,
    outfit_tpo: str | None = None,
    weights: dict[str, float] | None = None,
) -> list[str]:
    """코디의 추천 이유 2줄을 생성한다.

    기획서 섹션 6.4 구현.

    Args:
        scores: 5축 점수 (pcf, of, ch, pe, sf)
        user_tone_id: 사용자 톤 ID (pcf 템플릿용)
        outfit_tpo: 코디 TPO (of 템플릿용)
        weights: 가중치 오버라이드

    Returns:
        2줄의 자연어 추천 이유 리스트
    """
    if not scores:
        return []

    top_axes = _select_top_axes(scores, weights)

    tone_name: str | None = None
    if user_tone_id:
        tone_names = _load_tone_names()
        tone_name = tone_names.get(user_tone_id)

    reasons: list[str] = []
    for axis, raw_score, _ in top_axes:
        reason = _render_template(axis, raw_score, tone_name, outfit_tpo)
        reasons.append(reason)

    return reasons
