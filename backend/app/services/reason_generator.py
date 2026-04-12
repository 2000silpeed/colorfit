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
    n: int = 5,
) -> list[str]:
    """코디의 추천 이유를 생성한다. 기본 5축 전체."""
    if not scores:
        return []

    top_axes = _select_top_axes(scores, weights, n=n)

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


# ── 축별 상세 해설 ──

EXPLANATIONS: dict[str, dict[str, list[str]]] = {
    "pcf": {
        "high": [
            "{tone_name} 팔레트의 핵심 색상이 이 코디에 잘 반영되어 있어요. 피부 톤과 자연스럽게 어우러져 얼굴이 밝아 보이는 효과가 있어요.",
            "이 코디의 주요 색상이 {tone_name} 베스트 컬러에 가까워요. 피부의 따뜻함(또는 차가움)을 살려주는 색감이라 생기 있어 보여요.",
            "{tone_name} 진단 결과 기준으로, 이 조합의 색상들은 피부 톤과 RGB 거리가 가까운 편이에요. 얼굴색과 조화를 이루면서 세련된 인상을 줘요.",
        ],
        "mid": [
            "퍼스널컬러와 완전히 일치하진 않지만, 전체적으로 무난하게 어울리는 색감이에요. 포인트 아이템이 톤을 잡아줘요.",
            "{tone_name} 팔레트 색상과 약간의 거리가 있지만, 중성 톤 위주 구성이라 크게 벗어나지 않아요.",
            "핵심 컬러 대신 호환 컬러 위주로 구성되어 있어요. 부담 없으면서도 톤에서 크게 벗어나지 않는 안전한 조합이에요.",
        ],
        "low": [
            "퍼스널컬러와는 다소 거리가 있는 색감이에요. 하지만 다른 장점이 이를 보완해줘요.",
        ],
    },
    "of": {
        "high": [
            "{tpo} 상황에 딱 맞는 포멀도와 무드를 갖추고 있어요. 이 코디라면 분위기에 자연스럽게 녹아들 수 있어요.",
            "{tpo}에 필요한 드레스 코드를 잘 반영한 구성이에요. 격식과 편안함의 밸런스가 좋아요.",
            "이 코디의 실루엣과 소재감이 {tpo} 분위기에 최적화되어 있어요. 상황에 맞는 센스 있는 선택이에요.",
        ],
        "mid": [
            "특정 TPO에 한정되기보다는 다양한 상황에서 활용할 수 있는 범용적인 스타일이에요.",
            "여러 상황에 걸쳐 무난하게 소화할 수 있는 구성이에요. 데일리 코디로 활용도가 높아요.",
            "일상적인 상황 대부분에 어울리는 편안한 코디예요. 특별한 TPO 없이도 활용 가능해요.",
        ],
        "low": [
            "이 TPO에 최적화된 구성은 아니지만, 자신만의 스타일로 소화할 수 있어요.",
        ],
    },
    "ch": {
        "high": [
            "아이템들의 색상이 톤온톤 또는 보색 조화를 이루고 있어요. 채도 분산이 낮아 시각적으로 안정감이 있어요.",
            "메인 컬러와 서브 컬러가 자연스럽게 연결돼요. 색상 간 RGB 거리가 적절해서 통일감이 있으면서도 단조롭지 않아요.",
            "전체적으로 색감의 밸런스가 잘 잡혀 있어요. 포인트 컬러가 과하지 않게 전체 무드를 살려줘요.",
        ],
        "mid": [
            "전체적으로 무난한 색상 배합이에요. 채도가 비슷한 톤으로 구성되어 부담 없이 입기 좋아요.",
            "차분한 색감 위주로 정리되어 있어요. 강한 대비는 없지만 편안한 인상을 줘요.",
            "색상 조합이 크게 튀지 않는 안정적인 구성이에요. 데일리로 부담 없이 활용할 수 있어요.",
        ],
        "low": [
            "색상 배합이 다소 대비가 강하거나 유사색이 겹쳐요. 스타일링 포인트로 활용하면 오히려 개성 있어요.",
        ],
    },
    "pe": {
        "high": [
            "설정한 예산 범위 안에서 효율적으로 구성된 코디예요. 가격 대비 완성도가 높아요.",
            "합리적인 가격대의 아이템들로 스타일을 완성해요. 부담 없는 예산으로 높은 만족도를 기대할 수 있어요.",
            "예산을 알뜰하게 활용한 조합이에요. 핵심 아이템에 투자하고 나머지는 가성비로 채웠어요.",
        ],
        "mid": [
            "예산 범위에 대체로 맞는 구성이에요. 일부 아이템은 예산을 약간 넘을 수 있지만 전체적으로 합리적이에요.",
            "가격과 스타일 사이에서 적절한 밸런스를 찾은 조합이에요.",
        ],
        "low": [
            "예산 범위를 다소 벗어나는 구성이에요. 대체 아이템을 활용하면 가격을 조절할 수 있어요.",
        ],
    },
    "sf": {
        "high": [
            "상하의 실루엣 밸런스가 잘 잡혀 있어요. 카테고리 궁합이 좋고, 포멀도가 통일된 세련된 조합이에요.",
            "각 아이템이 서로의 장점을 살려주는 구성이에요. 핏감의 완급 조절이 잘 되어 있어서 전체적으로 정돈된 느낌이에요.",
            "레이어링이 자연스럽고 아이템 간 스타일 코드가 일치해요. 하나의 무드로 통일된 완성도 높은 코디예요.",
        ],
        "mid": [
            "기본에 충실한 안정적인 구성이에요. 무난하면서도 깔끔한 실루엣을 유지하고 있어요.",
            "편하게 입기 좋은 실용적인 조합이에요. 데일리 코디로 부담 없이 소화할 수 있어요.",
        ],
        "low": [
            "스타일 믹스가 다소 있지만, 의도적인 믹스매치로 개성을 살릴 수 있는 조합이에요.",
        ],
    },
}

AXIS_LABELS: dict[str, str] = {
    "pcf": "퍼스널컬러",
    "of": "TPO 적합",
    "ch": "색상 조화",
    "pe": "가격 효율",
    "sf": "스타일 핏",
}


def _score_level(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "mid"
    return "low"


def generate_score_explanations(
    scores: dict[str, float],
    user_tone_id: str | None = None,
    outfit_tpo: str | None = None,
    outfit_id: str | None = None,
) -> dict[str, str]:
    """5축 각각에 대한 상세 해설을 생성한다."""
    if not scores:
        return {}

    tone_name: str | None = None
    if user_tone_id:
        tone_names = _load_tone_names()
        tone_name = tone_names.get(user_tone_id)

    seed = outfit_id or str(scores.get("pcf", 0))
    result: dict[str, str] = {}

    for axis in DEFAULT_WEIGHTS:
        raw = scores.get(axis, 0.0)
        level = _score_level(raw)
        templates = EXPLANATIONS[axis][level]
        template = _deterministic_pick(templates, f"{seed}_{axis}_exp_{level}")

        if "{tone_name}" in template:
            name = tone_name or "퍼스널컬러"
            text = template.format(tone_name=name)
        elif "{tpo}" in template:
            tpo_name = TPO_NAMES_KO.get(outfit_tpo, outfit_tpo) if outfit_tpo else "일상"
            text = template.format(tpo=tpo_name)
        else:
            text = template

        result[axis] = text

    return result
