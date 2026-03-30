"""추출된 색상을 12-tone 팔레트에 매핑한다.

RGB 유클리드 거리 기반으로 가장 가까운 톤을 선정.
기획서 섹션 7.1 알고리즘 구현.
"""

import json
import logging
import math
from pathlib import Path

logger = logging.getLogger(__name__)

PALETTES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "palettes"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """HEX → RGB 변환."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """두 RGB 색상 간 유클리드 거리."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


class TonePalette:
    """12-tone 팔레트를 로드하고 색상 매칭을 수행한다."""

    def __init__(self, palettes_dir: Path = PALETTES_DIR) -> None:
        self.tones: dict[str, list[tuple[int, int, int]]] = {}
        self._load_palettes(palettes_dir)

    def _load_palettes(self, palettes_dir: Path) -> None:
        """팔레트 JSON 파일들을 로드한다."""
        for path in sorted(palettes_dir.glob("*.json")):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            tone_id = data["tone_id"]
            colors = [tuple(c["rgb"]) for c in data["colors"]]
            self.tones[tone_id] = colors
        logger.info("팔레트 로드: %d개 톤", len(self.tones))

    def match_color(self, hex_color: str) -> tuple[str, float]:
        """HEX 색상을 가장 가까운 톤에 매핑한다.

        Args:
            hex_color: HEX 색상 (예: "#B0A6C6")

        Returns:
            (tone_id, min_distance) 튜플
        """
        rgb = _hex_to_rgb(hex_color)
        best_tone = ""
        best_dist = float("inf")

        for tone_id, palette_colors in self.tones.items():
            min_dist = min(_rgb_distance(rgb, pc) for pc in palette_colors)
            if min_dist < best_dist:
                best_dist = min_dist
                best_tone = tone_id

        return best_tone, best_dist

    def match_dominant_colors(
        self, hex_colors: list[str]
    ) -> tuple[str, str]:
        """여러 dominant color 중 대표 톤을 결정한다.

        첫 번째 색상(가장 비중 큰 클러스터)의 매칭 결과를 대표로 사용한다.

        Args:
            hex_colors: dominant color HEX 리스트 (비중 순)

        Returns:
            (tone_id, primary_color_hex) 튜플.
            빈 리스트이면 ("", "")
        """
        if not hex_colors:
            return "", ""

        primary = hex_colors[0]
        tone_id, _ = self.match_color(primary)
        return tone_id, primary
