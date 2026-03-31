"""코디 스코어링 5축 함수.

각 함수는 순수 함수로, DB 의존 없이 동작한다.
기획서 섹션 5.5 참조.
"""

from pathlib import Path

import colorsys
from itertools import combinations
from statistics import stdev

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

    expanded_tpos = _expand_tpos(user_tpo_list)
    outfit_tag_set = set(outfit_tags)
    match_count = len(outfit_tag_set & expanded_tpos)
    total_tags = len(outfit_tag_set)

    if match_count >= 2:
        return min(100.0, round(80.0 + (match_count / total_tags) * 20.0, 2))
    elif match_count == 1:
        return round(60.0 + (1.0 / total_tags) * 20.0, 2)
    else:
        return 30.0


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
