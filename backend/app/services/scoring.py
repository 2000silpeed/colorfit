"""코디 스코어링 5축 함수.

각 함수는 순수 함수로, DB 의존 없이 동작한다.
기획서 섹션 5.5 참조.
"""

from __future__ import annotations

import json
from pathlib import Path

import colorsys
from itertools import combinations
from statistics import pstdev, stdev
from typing import Any

from app.services.color_matcher import TonePalette, _hex_to_rgb, _rgb_distance

PALETTES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "palettes"

_DISTANCE_DIVISOR = 4.42  # 기획서 명시값: max RGB 거리 441.67 / 100

COMPATIBLE_TONES: dict[str, set[str]] = {
    "spring_warm_light": {"spring_warm_bright", "spring_warm_vivid"},
    "spring_warm_bright": {"spring_warm_light", "spring_warm_vivid"},
    "spring_warm_vivid": {"spring_warm_light", "spring_warm_bright"},
    "summer_cool_light": {"summer_cool_soft", "summer_cool_bright", "summer_cool_mute"},
    "summer_cool_soft": {"summer_cool_light", "summer_cool_bright", "summer_cool_mute"},
    "summer_cool_bright": {"summer_cool_light", "summer_cool_soft", "summer_cool_mute"},
    "summer_cool_mute": {"summer_cool_light", "summer_cool_soft", "summer_cool_bright"},
    "autumn_warm_deep": {"autumn_warm_mute", "autumn_warm_strong"},
    "autumn_warm_mute": {"autumn_warm_deep", "autumn_warm_strong"},
    "autumn_warm_strong": {"autumn_warm_deep", "autumn_warm_mute"},
    "winter_cool_deep": {"winter_cool_strong", "winter_cool_vivid"},
    "winter_cool_strong": {"winter_cool_deep", "winter_cool_vivid"},
    "winter_cool_vivid": {"winter_cool_deep", "winter_cool_strong"},
}

_palette: TonePalette | None = None


def _get_palette() -> TonePalette:
    global _palette
    if _palette is None:
        _palette = TonePalette(PALETTES_DIR)
    return _palette


def _item_pcf(
    item_tone_id: str,
    item_hex_color: str,
    user_tone_id: str,
    palette: TonePalette,
) -> float:
    """단일 아이템의 PCF 점수를 계산한다.

    1단계: 톤 레벨 매칭 (동일 100, 호환 95)
    2단계: 색상 레벨 매칭 (RGB 유클리드 거리 → 점수)
    """
    if item_tone_id == user_tone_id:
        return 100.0

    compatible = COMPATIBLE_TONES.get(user_tone_id, set())
    if item_tone_id in compatible:
        return 95.0

    user_palette_colors = palette.tones.get(user_tone_id, [])
    if not user_palette_colors:
        return 0.0

    item_rgb = _hex_to_rgb(item_hex_color)
    d_min = min(_rgb_distance(item_rgb, pc) for pc in user_palette_colors)
    return max(0.0, 100.0 - (d_min / _DISTANCE_DIVISOR))


def calculate_pcf(
    item_tone_ids: list[str],
    item_hex_colors: list[str],
    user_tone_id: str,
    palette: TonePalette | None = None,
) -> float:
    """코디 전체 PCF(Personal Color Fit) 스코어를 계산한다.

    기획서 섹션 5.5.1 구현.

    Args:
        item_tone_ids: 코디 아이템들의 톤 ID 리스트
        item_hex_colors: 코디 아이템들의 HEX 색상 리스트
        user_tone_id: 사용자의 퍼스널컬러 톤 ID

    Returns:
        0~100 범위의 PCF 점수 (아이템별 점수의 평균)
    """
    if len(item_tone_ids) != len(item_hex_colors):
        raise ValueError(
            f"item_tone_ids({len(item_tone_ids)})와 "
            f"item_hex_colors({len(item_hex_colors)}) 길이가 다릅니다."
        )

    if not item_tone_ids:
        return 0.0

    pal = palette or _get_palette()

    scores = [
        _item_pcf(tone_id, hex_color, user_tone_id, pal)
        for tone_id, hex_color in zip(item_tone_ids, item_hex_colors)
    ]
    return round(sum(scores) / len(scores), 2)


# ---------------------------------------------------------------------------
# OF (Occasion Fit) — TPO 적합도  (기획서 섹션 5.5.2)
# ---------------------------------------------------------------------------

TPO_SYNONYMS: dict[str, set[str]] = {
    "commute": {"office", "commute"},
    "office": {"office", "commute"},
    "weekend": {"casual", "weekend", "daily"},
    "casual": {"casual", "weekend", "daily"},
    "daily": {"casual", "daily", "weekend"},
    "interview": {"interview", "office"},
    "campus": {"campus", "casual"},
    "event": {"party", "wedding", "event"},
    "party": {"party", "event"},
    "wedding": {"wedding", "event"},
    "workout": {"workout"},
    "date": {"date"},
    "travel": {"travel"},
}


def _expand_tpos(tpo_list: list[str]) -> set[str]:
    """사용자 TPO 리스트를 동의어 확장하여 집합으로 반환한다."""
    expanded: set[str] = set()
    for tpo in tpo_list:
        synonyms = TPO_SYNONYMS.get(tpo)
        if synonyms:
            expanded.update(synonyms)
        else:
            expanded.add(tpo)
    return expanded


def calculate_of(
    outfit_tags: list[str],
    user_tpo_list: list[str],
) -> float:
    """코디의 OF(Occasion Fit) 스코어를 계산한다.

    기획서 섹션 5.5.2 구현.

    Args:
        outfit_tags: 코디에 부여된 TPO 태그 리스트
        user_tpo_list: 사용자가 설정한 TPO 리스트

    Returns:
        30~100 범위의 OF 점수 (30점 하한)
    """
    if not outfit_tags or not user_tpo_list:
        return 30.0

    all_known_tpos = set()
    for syns in TPO_SYNONYMS.values():
        all_known_tpos.update(syns)

    outfit_tpos = set(outfit_tags) & all_known_tpos
    if not outfit_tpos:
        return 30.0

    user_set = set(user_tpo_list)

    # TPO 간 유사도 매트릭스 (0~1, 높을수록 유사)
    TPO_SIMILARITY: dict[tuple[str, str], float] = {
        ("commute", "office"): 0.9,
        ("commute", "interview"): 0.7,
        ("office", "interview"): 0.8,
        ("weekend", "casual"): 0.9,
        ("weekend", "campus"): 0.7,
        ("casual", "campus"): 0.8,
        ("casual", "date"): 0.5,
        ("date", "event"): 0.4,
        ("event", "wedding"): 0.8,
        ("event", "party"): 0.9,
        ("campus", "date"): 0.5,
        ("travel", "casual"): 0.6,
        ("travel", "weekend"): 0.6,
        ("workout", "casual"): 0.3,
    }

    def _tpo_similarity(a: str, b: str) -> float:
        if a == b:
            return 1.0
        key = (min(a, b), max(a, b))
        rev_key = (max(a, b), min(a, b))
        return TPO_SIMILARITY.get(key, TPO_SIMILARITY.get(rev_key, 0.0))

    best_sim = 0.0
    for o_tpo in outfit_tpos:
        for u_tpo in user_set:
            sim = _tpo_similarity(o_tpo, u_tpo)
            if sim > best_sim:
                best_sim = sim

    # 유사도 → 점수 변환 (30~100 범위)
    # 1.0 → 100, 0.9 → 95, 0.7 → 79, 0.5 → 65, 0.3 → 51, 0.0 → 30
    return round(30.0 + best_sim * 70.0, 1)


# ---------------------------------------------------------------------------
# CH (Color Harmony) — 색상 조화도  (기획서 섹션 5.5.3)
# ---------------------------------------------------------------------------


def _saturation(hex_color: str) -> float:
    """HEX 색상의 HSV 채도(Saturation) 값을 반환한다 (0.0~1.0)."""
    r, g, b = _hex_to_rgb(hex_color)
    _, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return s


def _distance_score(d_avg: float) -> float:
    """평균 RGB 거리를 기반으로 구간별 점수를 산출한다."""
    if d_avg < 30:
        return 60.0
    elif d_avg < 80:
        return 80.0 + (d_avg - 30) / 50 * 20.0
    elif d_avg < 150:
        return 100.0 - (d_avg - 80) / 70 * 21.0
    else:
        return max(30.0, 79.0 - (d_avg - 150) / 290 * 49.0)


def calculate_ch(item_hex_colors: list[str]) -> float:
    """코디의 CH(Color Harmony) 스코어를 계산한다.

    기획서 섹션 5.5.3 구현.

    Args:
        item_hex_colors: 코디 아이템들의 HEX 색상 리스트

    Returns:
        0~100 범위의 CH 점수
    """
    if len(item_hex_colors) < 2:
        return 50.0

    rgbs = [_hex_to_rgb(c) for c in item_hex_colors]
    distances = [_rgb_distance(a, b) for a, b in combinations(rgbs, 2)]
    d_avg = sum(distances) / len(distances)

    score = _distance_score(d_avg)

    if len(item_hex_colors) >= 3:
        sats = [_saturation(c) for c in item_hex_colors]
        sat_std = stdev(sats)
        if 0.15 <= sat_std <= 0.40:
            score += 5.0

    return round(min(100.0, max(0.0, score)), 2)


# ---------------------------------------------------------------------------
# PE (Price Efficiency) — 가격 효율성  (기획서 섹션 5.5.4)
# ---------------------------------------------------------------------------


def calculate_pe(
    total_price: float,
    budget_min: float,
    budget_max: float,
) -> float:
    """코디의 PE(Price Efficiency) 스코어를 계산한다.

    기획서 섹션 5.5.4 구현.

    Args:
        total_price: 코디 총 가격
        budget_min: 사용자 최소 예산
        budget_max: 사용자 최대 예산

    Returns:
        0~100 범위의 PE 점수
    """
    if budget_min <= 0 or budget_max <= 0 or budget_max < budget_min:
        return 0.0

    budget_mid = (budget_min + budget_max) / 2

    if budget_min <= total_price <= budget_max:
        # Case 1: 예산 범위 내 — 중앙 가까울수록 높은 점수
        score = 100.0 - abs(total_price - budget_mid) / budget_mid * 30.0
    elif total_price > budget_max:
        # Case 2: 예산 초과 — 급격한 감점
        over_ratio = (total_price - budget_max) / budget_max
        score = 70.0 - over_ratio * 100.0
    else:
        # Case 3: 예산 미만 — 완만한 감점, 최저 40점
        under_ratio = (budget_min - total_price) / budget_min
        score = 80.0 - under_ratio * 80.0

    if total_price < budget_min:
        return round(max(40.0, score), 2)

    return round(max(0.0, min(100.0, score)), 2)


# ---------------------------------------------------------------------------
# SF (Style Fit) — 스타일 적합도  (기획서 섹션 5.5.5 / 6.6)
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_style_compat: dict[str, int] | None = None
_silhouette_rules: dict[str, dict[str, Any]] | None = None
_formality_map: dict[str, int] | None = None


def _load_style_compat() -> dict[str, int]:
    global _style_compat
    if _style_compat is None:
        with open(DATA_DIR / "style_compat.json", encoding="utf-8") as f:
            raw = json.load(f)
        _style_compat = {k: v for k, v in raw.items() if not k.startswith("_")}
    return _style_compat


def _load_silhouette_rules() -> dict[str, dict[str, Any]]:
    global _silhouette_rules
    if _silhouette_rules is None:
        with open(DATA_DIR / "silhouette_rules.json", encoding="utf-8") as f:
            raw = json.load(f)
        _silhouette_rules = {k: v for k, v in raw.items() if not k.startswith("_")}
    return _silhouette_rules


def _load_formality_map() -> dict[str, int]:
    global _formality_map
    if _formality_map is None:
        with open(DATA_DIR / "formality_map.json", encoding="utf-8") as f:
            raw = json.load(f)
        _formality_map = {k: v for k, v in raw.items() if not k.startswith("_")}
    return _formality_map


def _compat_key(cat_a: str, cat_b: str) -> str:
    """두 카테고리로 궁합 매트릭스 조회 키를 생성한다."""
    return f"{cat_a}:{cat_b}"


def _category_compat_score(categories: list[str]) -> float:
    """카테고리 궁합 점수 (0~100). 모든 2-조합의 평균."""
    if len(categories) < 2:
        return 70.0

    compat = _load_style_compat()
    scores: list[float] = []

    for a, b in combinations(categories, 2):
        key = _compat_key(a, b)
        rev_key = _compat_key(b, a)
        score = compat.get(key) or compat.get(rev_key)
        if score is not None:
            scores.append(float(score))
        else:
            scores.append(60.0)

    return sum(scores) / len(scores)


def _silhouette_balance_score(
    top_silhouette: str | None,
    bottom_silhouette: str | None,
) -> float:
    """실루엣 밸런스 점수 (0~100). 상의-하의 조합 규칙 기반."""
    if not top_silhouette or not bottom_silhouette:
        return 70.0

    rules = _load_silhouette_rules()
    key = f"{top_silhouette}:{bottom_silhouette}"
    rule = rules.get(key)

    if rule is not None:
        return float(rule["score"])

    return 70.0


def _formality_consistency_score(categories: list[str]) -> float:
    """포멀도 일관성 점수 (0~100). 표준편차 기반 감점."""
    if len(categories) < 2:
        return 100.0

    fmap = _load_formality_map()
    formalities = [float(fmap.get(cat, 3)) for cat in categories]

    std_dev = pstdev(formalities)
    return round(max(0.0, 100.0 - std_dev * 40.0), 2)


def calculate_sf(
    categories: list[str],
    top_silhouette: str | None = None,
    bottom_silhouette: str | None = None,
) -> float:
    """코디의 SF(Style Fit) 스코어를 계산한다.

    기획서 섹션 5.5.5 / 6.6 구현.

    Args:
        categories: 코디 아이템들의 카테고리 리스트 (e.g. ["블라우스", "슬랙스", "로퍼"])
        top_silhouette: 상의 실루엣 (e.g. "fitted", "oversized")
        bottom_silhouette: 하의 실루엣 (e.g. "slim", "wide")

    Returns:
        0~100 범위의 SF 점수
    """
    if not categories:
        return 0.0

    cat_score = _category_compat_score(categories)
    sil_score = _silhouette_balance_score(top_silhouette, bottom_silhouette)
    form_score = _formality_consistency_score(categories)

    sf = cat_score * 0.50 + sil_score * 0.25 + form_score * 0.25
    return round(max(0.0, min(100.0, sf)), 2)
