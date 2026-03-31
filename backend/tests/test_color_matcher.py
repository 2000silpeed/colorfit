"""color_matcher 서비스 테스트."""

import json
import pytest
from pathlib import Path

from app.services.color_matcher import TonePalette, _hex_to_rgb, _rgb_distance


class TestHexToRgb:
    def test_basic(self):
        assert _hex_to_rgb("#FF0000") == (255, 0, 0)
        assert _hex_to_rgb("#00FF00") == (0, 255, 0)
        assert _hex_to_rgb("#0000FF") == (0, 0, 255)

    def test_without_hash(self):
        assert _hex_to_rgb("B0A6C6") == (176, 166, 198)

    def test_mixed_case(self):
        assert _hex_to_rgb("#ff6b6b") == (255, 107, 107)


class TestRgbDistance:
    def test_same_color_zero(self):
        assert _rgb_distance((100, 100, 100), (100, 100, 100)) == 0.0

    def test_black_white(self):
        d = _rgb_distance((0, 0, 0), (255, 255, 255))
        assert abs(d - 441.67) < 1.0  # sqrt(3 * 255^2) ≈ 441.67

    def test_symmetry(self):
        d1 = _rgb_distance((100, 50, 200), (200, 100, 50))
        d2 = _rgb_distance((200, 100, 50), (100, 50, 200))
        assert d1 == d2


class TestTonePalette:
    @pytest.fixture
    def palette(self, tmp_path, monkeypatch):
        """테스트용 미니 팔레트를 생성한다."""
        monkeypatch.setattr(TonePalette, "EXPECTED_TONES", {"spring_warm_light", "winter_cool_deep"})
        tone_a = {
            "tone_id": "spring_warm_light",
            "colors": [
                {"hex": "#FADADD", "rgb": [250, 218, 221], "hsl": [354, 76, 92], "name_ko": "베이비 핑크"},
                {"hex": "#FFE4C4", "rgb": [255, 228, 196], "hsl": [33, 100, 88], "name_ko": "비스크"},
            ],
        }
        tone_b = {
            "tone_id": "winter_cool_deep",
            "colors": [
                {"hex": "#1E1E4E", "rgb": [30, 30, 78], "hsl": [240, 44, 21], "name_ko": "미드나이트"},
                {"hex": "#000080", "rgb": [0, 0, 128], "hsl": [240, 100, 25], "name_ko": "네이비"},
            ],
        }
        for tone in [tone_a, tone_b]:
            path = tmp_path / f"{tone['tone_id']}.json"
            with open(path, "w") as f:
                json.dump(tone, f)
        return TonePalette(palettes_dir=tmp_path)

    def test_loads_tones(self, palette):
        assert len(palette.tones) == 2
        assert "spring_warm_light" in palette.tones
        assert "winter_cool_deep" in palette.tones

    def test_match_warm_color(self, palette):
        tone_id, dist = palette.match_color("#FFD0D0")  # 밝은 핑크
        assert tone_id == "spring_warm_light"

    def test_match_dark_color(self, palette):
        tone_id, dist = palette.match_color("#0A0A50")  # 어두운 네이비
        assert tone_id == "winter_cool_deep"

    def test_match_dominant_colors(self, palette):
        colors = ["#FFD0D0", "#0A0A50"]  # 첫 번째가 대표
        tone_id, primary_hex = palette.match_dominant_colors(colors)
        assert tone_id == "spring_warm_light"
        assert primary_hex == "#FFD0D0"

    def test_match_dominant_colors_empty(self, palette):
        tone_id, primary_hex = palette.match_dominant_colors([])
        assert tone_id == ""
        assert primary_hex == ""

    def test_missing_palette_raises(self, tmp_path):
        """필수 팔레트 누락 시 FileNotFoundError."""
        tone = {
            "tone_id": "spring_warm_light",
            "colors": [{"hex": "#FADADD", "rgb": [250, 218, 221], "hsl": [354, 76, 92], "name_ko": "핑크"}],
        }
        path = tmp_path / "spring_warm_light.json"
        with open(path, "w") as f:
            json.dump(tone, f)
        with pytest.raises(FileNotFoundError, match="필수 톤 팔레트 누락"):
            TonePalette(palettes_dir=tmp_path)


class TestTonePaletteReal:
    """실제 팔레트 데이터로 검증한다."""

    @pytest.fixture
    def palette(self):
        palettes_dir = Path(__file__).resolve().parent.parent / "data" / "palettes"
        if not palettes_dir.exists():
            pytest.skip("팔레트 데이터 없음")
        return TonePalette(palettes_dir=palettes_dir)

    def test_all_13_tones_loaded(self, palette):
        assert len(palette.tones) == 13
        assert "summer_cool_soft" in palette.tones

    def test_warm_color_maps_to_warm_tone(self, palette):
        tone_id, _ = palette.match_color("#FF6B6B")  # 밝은 코랄/레드
        assert "warm" in tone_id or "bright" in tone_id

    def test_cool_dark_maps_to_cool_tone(self, palette):
        tone_id, _ = palette.match_color("#1E1E4E")  # 어두운 남색
        assert "cool" in tone_id or "deep" in tone_id
