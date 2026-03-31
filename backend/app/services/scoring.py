"""코디 스코어링 5축 함수.

각 함수는 순수 함수로, DB 의존 없이 동작한다.
기획서 섹션 5.5 참조.
"""

from pathlib import Path

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
