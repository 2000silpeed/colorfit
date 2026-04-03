"""추천 이유 생성 모듈.

기획서 섹션 6.4 구현.
5축 가중 기여도 상위 2개 축을 선정하여 자연어 추천 이유를 생성한다.
같은 축이라도 여러 변형 템플릿 중 랜덤 선택하여 다양성을 확보한다.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PALETTES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "palettes"

DEFAULT_WEIGHTS: dict[str, float] = {
    "pcf": 0.25,
    "of": 0.20,
    "ch": 0.15,
    "pe": 0.15,
    "sf": 0.25,
}

TEMPLATES: dict[str, dict[str, list[str]]] = {
    "pcf": {
        "high": [
            "{tone_name} 핵심 컬러와 잘 어울려서 피부톤이 한층 밝아 보여요",
            "{tone_name} 톤에 딱 맞는 색감으로 세련된 느낌이에요",
            "퍼스널컬러와 찰떡궁합! 얼굴이 화사해 보이는 조합이에요",
            "{tone_name} 베스트 컬러가 포함된 코디예요",
            "피부 톤을 살려주는 컬러 매칭이 돋보여요",
            "이 색감이면 피부가 맑아 보이는 효과가 있어요",
            "{tone_name} 팔레트에서 엄선한 컬러 조합이에요",
            "얼굴에 생기를 더해주는 {tone_name} 컬러예요",
            "피부 톤과 조화로운 색상으로 자연스러워요",
            "컬러 진단 결과에 최적화된 색감이에요",
        ],
        "mid": [
            "퍼스널컬러와 비교적 잘 어울리는 색상 구성이에요",
            "무난하면서도 톤에 맞는 컬러 조합이에요",
            "퍼스널컬러 기반으로 선별된 색감이에요",
            "톤에 크게 벗어나지 않는 안전한 컬러예요",
            "퍼스널컬러를 은은하게 반영한 조합이에요",
            "컬러 톤이 자연스럽게 어우러져요",
        ],
    },
    "of": {
        "high": [
            "{tpo} 룩에 적합한 스타일링이에요",
            "{tpo}에 입고 가면 센스 있어 보여요",
            "{tpo} 상황에 딱 맞는 무드예요",
            "{tpo} 때 이 조합이면 완벽해요",
            "{tpo} 분위기에 자연스럽게 녹아드는 스타일이에요",
            "{tpo}에 어울리는 포멀도와 무드를 갖췄어요",
            "이런 날 입으면 {tpo} 분위기가 살아요",
            "{tpo} 코드에 맞춘 스마트한 선택이에요",
        ],
        "mid": [
            "다양한 상황에 무난하게 활용할 수 있는 스타일이에요",
            "여러 TPO에 걸쳐 활용도가 높은 코디예요",
            "일상에서 편하게 소화할 수 있는 구성이에요",
            "상황을 크게 가리지 않는 만능 코디예요",
            "어디에 입고 가도 자연스러운 스타일이에요",
            "데일리로 활용하기 좋은 범용 코디예요",
        ],
    },
    "ch": {
        "high": [
            "메인-서브 컬러가 균형 있게 조화를 이뤄요",
            "컬러 배합이 세련되고 안정감 있어요",
            "톤온톤 컬러 매칭으로 깔끔한 인상이에요",
            "색상 조화가 자연스럽고 고급스러워요",
            "아이템끼리 컬러가 서로 잘 받쳐줘요",
            "컬러 밸런스가 좋아서 눈에 편안해요",
            "포인트 컬러가 전체 분위기를 살려줘요",
            "색감의 통일감이 코디 완성도를 높여요",
        ],
        "mid": [
            "전체적으로 안정감 있는 색상 배합이에요",
            "무난하면서 편안한 컬러 구성이에요",
            "부담 없는 컬러 조합으로 데일리에 좋아요",
            "차분한 색감으로 깔끔하게 정리돼요",
            "색상이 튀지 않아서 무난하게 입기 좋아요",
            "자연스러운 톤으로 부담 없는 조합이에요",
        ],
    },
    "pe": {
        "high": [
            "예산 범위 내에서 가성비 좋은 조합이에요",
            "합리적인 가격대로 스타일을 완성할 수 있어요",
            "가격 대비 퀄리티가 좋은 아이템들이에요",
            "부담 없는 가격에 완성도 높은 코디예요",
            "스마트한 가격으로 트렌디한 룩을 연출해요",
            "가성비를 챙기면서도 스타일을 놓치지 않았어요",
            "예산 안에서 최적의 조합을 찾았어요",
            "실속 있는 가격대의 알찬 구성이에요",
        ],
        "mid": [
            "가격 대비 만족스러운 구성이에요",
            "적당한 가격대의 균형 잡힌 조합이에요",
            "가격과 스타일 사이에서 적절한 밸런스예요",
            "무리 없는 가격대로 구성했어요",
            "합리적인 가격 범위의 조합이에요",
        ],
    },
    "sf": {
        "high": [
            "아이템 간 스타일 밸런스가 좋아요",
            "상하의 실루엣이 잘 어울리는 조합이에요",
            "카테고리 구성이 완성도 높아요",
            "전체적인 무드가 통일감 있어요",
            "깔끔하게 정리된 스타일링이에요",
            "실루엣 라인이 자연스럽게 이어져요",
            "아이템 궁합이 잘 맞는 조합이에요",
            "각 피스가 서로를 잘 보완해주는 코디예요",
            "핏감의 완급 조절이 잘 된 스타일이에요",
            "레이어링이 자연스럽고 세련돼요",
        ],
        "mid": [
            "전체적으로 무난한 스타일 구성이에요",
            "기본에 충실한 안정적인 조합이에요",
            "편하게 입기 좋은 실용적인 코디예요",
            "데일리로 부담 없이 소화할 수 있어요",
            "기본템 위주로 깔끔하게 정리한 코디예요",
            "심플하면서도 정돈된 느낌이에요",
        ],
    },
}

_tone_names: dict[str, str] | None = None


def _load_tone_names() -> dict[str, str]:
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


def _deterministic_pick(templates: list[str], seed: str) -> str:
    """시드 기반으로 템플릿을 결정적으로 선택 (같은 코디는 항상 같은 문구)."""
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(templates)
    return templates[idx]


def _select_top_axes(
    scores: dict[str, float],
    weights: dict[str, float] | None = None,
    n: int = 2,
) -> list[tuple[str, float, float]]:
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
    seed: str,
    tone_name: str | None = None,
    tpo: str | None = None,
) -> str:
    level = "high" if raw_score >= 75 else "mid"
    templates = TEMPLATES[axis][level]
    template = _deterministic_pick(templates, f"{seed}_{axis}_{level}")

    if axis == "pcf" and "{tone_name}" in template:
        name = tone_name or "퍼스널컬러"
        return template.format(tone_name=name)

    if axis == "of" and "{tpo}" in template:
        tpo_name = TPO_NAMES_KO.get(tpo, tpo) if tpo else "일상"
        return template.format(tpo=tpo_name)

    return template


def generate_reasons(
    scores: dict[str, float],
    user_tone_id: str | None = None,
    outfit_tpo: str | None = None,
    outfit_id: str | None = None,
    weights: dict[str, float] | None = None,
) -> list[str]:
    """코디의 추천 이유 2줄을 생성한다."""
    if not scores:
        return []

    top_axes = _select_top_axes(scores, weights)

    tone_name: str | None = None
    if user_tone_id:
        tone_names = _load_tone_names()
        tone_name = tone_names.get(user_tone_id)

    seed = outfit_id or str(scores.get("pcf", 0))

    reasons: list[str] = []
    for axis, raw_score, _ in top_axes:
        reason = _render_template(axis, raw_score, seed, tone_name, outfit_tpo)
        reasons.append(reason)

    return reasons
