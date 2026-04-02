"""옷 사진 분석 서비스.

업로드된 옷 사진에서 색상을 추출하고 사용자 퍼스널컬러와 비교하여
PCF 점수 + 채도/명도 세부 점수를 산출한다.
기획서 섹션 5.5.1 (PCF 계산 로직 재사용).
"""

from __future__ import annotations

import colorsys
import logging
from pathlib import Path

from app.services.color_extractor import extract_colors_from_url
from app.services.color_matcher import TonePalette, _hex_to_rgb
from app.services.scoring import (
    COMPATIBLE_TONES,
    _item_pcf,
    _get_palette,
)

logger = logging.getLogger(__name__)

TONE_NAMES_KO: dict[str, str] = {
    "spring_warm_light": "봄 웜 라이트",
    "spring_warm_bright": "봄 웜 브라이트",
    "spring_warm_vivid": "봄 웜 비비드",
    "summer_cool_light": "여름 쿨 라이트",
    "summer_cool_soft": "여름 쿨 소프트",
    "summer_cool_bright": "여름 쿨 브라이트",
    "summer_cool_mute": "여름 쿨 뮤트",
    "autumn_warm_deep": "가을 웜 딥",
    "autumn_warm_mute": "가을 웜 뮤트",
    "autumn_warm_strong": "가을 웜 스트롱",
    "winter_cool_deep": "겨울 쿨 딥",
    "winter_cool_strong": "겨울 쿨 스트롱",
    "winter_cool_vivid": "겨울 쿨 비비드",
}


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    r, g, b = _hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return h, s, l


def _saturation_score(hex_colors: list[str], user_tone_id: str) -> float:
    """채도 적합도 점수 (0~100).

    사용자 톤의 이상적 채도 범위와 비교.
    """
    if not hex_colors:
        return 50.0

    tone_saturation_range: dict[str, tuple[float, float]] = {
        "spring_warm_light": (0.3, 0.6),
        "spring_warm_bright": (0.5, 0.8),
        "spring_warm_vivid": (0.7, 1.0),
        "summer_cool_light": (0.2, 0.5),
        "summer_cool_soft": (0.15, 0.45),
        "summer_cool_bright": (0.4, 0.7),
        "summer_cool_mute": (0.1, 0.4),
        "autumn_warm_deep": (0.3, 0.6),
        "autumn_warm_mute": (0.15, 0.45),
        "autumn_warm_strong": (0.5, 0.8),
        "winter_cool_deep": (0.3, 0.7),
        "winter_cool_strong": (0.5, 0.9),
        "winter_cool_vivid": (0.7, 1.0),
    }

    ideal_min, ideal_max = tone_saturation_range.get(user_tone_id, (0.3, 0.7))

    saturations = [_hex_to_hsl(c)[1] for c in hex_colors]
    avg_sat = sum(saturations) / len(saturations)

    if ideal_min <= avg_sat <= ideal_max:
        return 100.0

    if avg_sat < ideal_min:
        diff = ideal_min - avg_sat
    else:
        diff = avg_sat - ideal_max

    return max(0.0, round(100.0 - diff * 200, 1))


def _lightness_score(hex_colors: list[str], user_tone_id: str) -> float:
    """명도 적합도 점수 (0~100).

    사용자 톤의 이상적 명도 범위와 비교.
    """
    if not hex_colors:
        return 50.0

    tone_lightness_range: dict[str, tuple[float, float]] = {
        "spring_warm_light": (0.6, 0.85),
        "spring_warm_bright": (0.5, 0.75),
        "spring_warm_vivid": (0.4, 0.65),
        "summer_cool_light": (0.65, 0.9),
        "summer_cool_soft": (0.55, 0.8),
        "summer_cool_bright": (0.5, 0.75),
        "summer_cool_mute": (0.5, 0.75),
        "autumn_warm_deep": (0.2, 0.45),
        "autumn_warm_mute": (0.35, 0.6),
        "autumn_warm_strong": (0.3, 0.55),
        "winter_cool_deep": (0.15, 0.4),
        "winter_cool_strong": (0.25, 0.5),
        "winter_cool_vivid": (0.35, 0.6),
    }

    ideal_min, ideal_max = tone_lightness_range.get(user_tone_id, (0.3, 0.7))

    lightnesses = [_hex_to_hsl(c)[2] for c in hex_colors]
    avg_light = sum(lightnesses) / len(lightnesses)

    if ideal_min <= avg_light <= ideal_max:
        return 100.0

    if avg_light < ideal_min:
        diff = ideal_min - avg_light
    else:
        diff = avg_light - ideal_max

    return max(0.0, round(100.0 - diff * 200, 1))


def _generate_reasons(
    pcf: float,
    sat_score: float,
    light_score: float,
    matched_tone_id: str,
    user_tone_id: str,
) -> list[str]:
    """점수별 상세 이유를 생성한다."""
    reasons: list[str] = []
    user_tone_name = TONE_NAMES_KO.get(user_tone_id, user_tone_id)
    matched_tone_name = TONE_NAMES_KO.get(matched_tone_id, matched_tone_id)

    if pcf >= 90:
        reasons.append(f"{user_tone_name} 톤과 완벽하게 어울리는 색상이에요.")
    elif pcf >= 75:
        reasons.append(f"{user_tone_name} 톤과 잘 어울리는 색상이에요.")
    elif pcf >= 50:
        reasons.append(
            f"이 옷의 색상({matched_tone_name})은 {user_tone_name} 톤과 "
            "보통 수준으로 어울려요."
        )
    else:
        reasons.append(
            f"이 옷의 색상({matched_tone_name})은 {user_tone_name} 톤과 "
            "잘 맞지 않을 수 있어요."
        )

    if sat_score >= 80:
        reasons.append("채도가 회원님의 톤에 적합해요.")
    elif sat_score < 50:
        reasons.append("채도가 회원님의 톤 범위를 벗어나요.")

    if light_score >= 80:
        reasons.append("명도도 톤에 잘 맞아요.")
    elif light_score < 50:
        reasons.append("명도가 회원님의 톤 범위와 다소 차이가 있어요.")

    return reasons


async def analyze_closet_item(
    image_url: str,
    user_tone_id: str,
) -> dict:
    """옷 사진을 분석하여 퍼스널컬러 적합도를 산출한다.

    Args:
        image_url: 분석할 옷 이미지 URL
        user_tone_id: 사용자의 퍼스널컬러 톤 ID

    Returns:
        dominant_colors, matched_tone_id, pcf_score,
        saturation_score, lightness_score, overall_score, reasons
    """
    hex_colors = extract_colors_from_url(image_url, n_colors=3)
    if not hex_colors:
        return {
            "dominant_colors": [],
            "matched_tone_id": "",
            "matched_tone_name": "",
            "pcf_score": 0.0,
            "saturation_score": 0.0,
            "lightness_score": 0.0,
            "overall_score": 0.0,
            "reasons": ["이미지에서 색상을 추출할 수 없었습니다."],
        }

    palette = _get_palette()
    matched_tone_id, _ = palette.match_dominant_colors(hex_colors)

    pcf = 0.0
    for hex_color in hex_colors:
        color_tone_id, _ = palette.match_color(hex_color)
        pcf += _item_pcf(color_tone_id, hex_color, user_tone_id, palette)
    pcf = round(pcf / len(hex_colors), 1)

    sat_score = _saturation_score(hex_colors, user_tone_id)
    light_score = _lightness_score(hex_colors, user_tone_id)

    overall = round(pcf * 0.5 + sat_score * 0.25 + light_score * 0.25, 1)

    reasons = _generate_reasons(
        pcf, sat_score, light_score, matched_tone_id, user_tone_id,
    )

    # 색상별 비율 (균등 분배 — K-means 클러스터 가중치는 extractor에서 미반환)
    total = len(hex_colors)
    ratios = [round(1.0 / total, 2)] * total
    if ratios:
        ratios[0] = round(1.0 - sum(ratios[1:]), 2)

    return {
        "dominant_colors": [
            {"hex": c, "ratio": r} for c, r in zip(hex_colors, ratios)
        ],
        "matched_tone_id": matched_tone_id,
        "matched_tone_name": TONE_NAMES_KO.get(matched_tone_id, matched_tone_id),
        "pcf_score": pcf,
        "saturation_score": sat_score,
        "lightness_score": light_score,
        "overall_score": overall,
        "reasons": reasons,
    }
