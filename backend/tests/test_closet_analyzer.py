"""Task 3.5 — 옷 사진 분석 서비스 테스트.

closet_analyzer의 순수 함수 + 통합 테스트.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.closet_analyzer import (
    _hex_to_hsl,
    _saturation_score,
    _lightness_score,
    _generate_reasons,
    analyze_closet_item,
    TONE_NAMES_KO,
)


# ── HSL 변환 ──


class TestHexToHsl:
    def test_pure_red(self):
        h, s, l = _hex_to_hsl("#FF0000")
        assert abs(h - 0.0) < 0.01
        assert abs(s - 1.0) < 0.01
        assert abs(l - 0.5) < 0.01

    def test_white(self):
        h, s, l = _hex_to_hsl("#FFFFFF")
        assert abs(s - 0.0) < 0.01
        assert abs(l - 1.0) < 0.01

    def test_black(self):
        h, s, l = _hex_to_hsl("#000000")
        assert abs(l - 0.0) < 0.01

    def test_pastel_pink(self):
        _, s, l = _hex_to_hsl("#FADADD")
        assert 0.0 < s < 1.0
        assert l > 0.8


# ── 채도 점수 ──


class TestSaturationScore:
    def test_in_range_returns_100(self):
        # spring_warm_light: ideal sat 0.3~0.6
        # 중간 채도 색상
        score = _saturation_score(["#D4A574"], "spring_warm_light")
        assert score > 0

    def test_empty_colors(self):
        score = _saturation_score([], "spring_warm_light")
        assert score == 50.0

    def test_low_saturation_penalized(self):
        # 거의 무채색 → 봄웜비비드(0.7~1.0)와는 채도 차이 큼
        score = _saturation_score(["#808080"], "spring_warm_vivid")
        assert score < 100.0

    def test_vivid_tone_high_saturation(self):
        # 높은 채도 색상 → 비비드 톤에 적합
        score = _saturation_score(["#FF0000"], "spring_warm_vivid")
        assert score >= 80.0

    def test_mute_tone_low_saturation(self):
        # 낮은 채도 → 뮤트 톤에 적합
        score = _saturation_score(["#C0B8B0"], "summer_cool_mute")
        assert score > 50.0


# ── 명도 점수 ──


class TestLightnessScore:
    def test_empty_colors(self):
        score = _lightness_score([], "spring_warm_light")
        assert score == 50.0

    def test_light_color_for_light_tone(self):
        # 밝은 색상 → 봄웜라이트(0.6~0.85)에 적합
        score = _lightness_score(["#F0E0D0"], "spring_warm_light")
        assert score >= 80.0

    def test_dark_color_for_deep_tone(self):
        # 어두운 색상 → 겨울쿨딥(0.15~0.4)에 적합
        score = _lightness_score(["#2C1A0E"], "winter_cool_deep")
        assert score > 50.0

    def test_dark_color_penalized_for_light_tone(self):
        # 어두운 색상 → 봄웜라이트에 안맞음
        score = _lightness_score(["#1A0E0A"], "spring_warm_light")
        assert score < 70.0


# ── 이유 생성 ──


class TestGenerateReasons:
    def test_high_pcf_reason(self):
        reasons = _generate_reasons(95.0, 90.0, 90.0, "spring_warm_light", "spring_warm_light")
        assert any("완벽" in r for r in reasons)

    def test_low_pcf_reason(self):
        reasons = _generate_reasons(30.0, 50.0, 50.0, "winter_cool_deep", "spring_warm_light")
        assert any("잘 맞지 않" in r for r in reasons)

    def test_sat_warning(self):
        reasons = _generate_reasons(80.0, 40.0, 80.0, "spring_warm_light", "spring_warm_light")
        assert any("채도" in r for r in reasons)

    def test_lightness_warning(self):
        reasons = _generate_reasons(80.0, 80.0, 40.0, "spring_warm_light", "spring_warm_light")
        assert any("명도" in r for r in reasons)

    def test_all_good(self):
        reasons = _generate_reasons(95.0, 90.0, 90.0, "spring_warm_light", "spring_warm_light")
        assert len(reasons) >= 2
        assert not any("벗어나" in r for r in reasons)

    def test_medium_pcf(self):
        reasons = _generate_reasons(65.0, 80.0, 80.0, "autumn_warm_deep", "spring_warm_light")
        assert any("보통" in r for r in reasons)

    def test_tone_names_used(self):
        reasons = _generate_reasons(95.0, 90.0, 90.0, "summer_cool_soft", "summer_cool_soft")
        assert any("여름 쿨 소프트" in r for r in reasons)


# ── 톤 이름 데이터 ──


class TestToneNames:
    def test_all_13_tones_have_names(self):
        expected_tones = [
            "spring_warm_light", "spring_warm_bright", "spring_warm_vivid",
            "summer_cool_light", "summer_cool_soft", "summer_cool_bright", "summer_cool_mute",
            "autumn_warm_deep", "autumn_warm_mute", "autumn_warm_strong",
            "winter_cool_deep", "winter_cool_strong", "winter_cool_vivid",
        ]
        for tone in expected_tones:
            assert tone in TONE_NAMES_KO, f"{tone} 누락"


# ── 통합: analyze_closet_item ──


class TestAnalyzeClosetItem:
    @pytest.mark.asyncio
    @patch("app.services.closet_analyzer.extract_colors_from_url")
    @patch("app.services.closet_analyzer._get_palette")
    async def test_successful_analysis(self, mock_palette, mock_extract):
        mock_extract.return_value = ["#F0E0D0", "#D4A574", "#C8B8A8"]

        palette_inst = MagicMock()
        palette_inst.match_dominant_colors.return_value = ("spring_warm_light", "#F0E0D0")
        palette_inst.match_color.return_value = ("spring_warm_light", 10.0)
        palette_inst.tones = {"spring_warm_light": [(240, 224, 208)]}
        mock_palette.return_value = palette_inst

        with patch("app.services.closet_analyzer._item_pcf", return_value=85.0):
            result = await analyze_closet_item(
                image_url="https://example.com/shirt.jpg",
                user_tone_id="spring_warm_light",
            )

        assert result["pcf_score"] == 85.0
        assert result["matched_tone_id"] == "spring_warm_light"
        assert result["matched_tone_name"] == "봄 웜 라이트"
        assert len(result["dominant_colors"]) == 3
        assert result["overall_score"] > 0
        assert len(result["reasons"]) >= 1

    @pytest.mark.asyncio
    @patch("app.services.closet_analyzer.extract_colors_from_url")
    async def test_no_colors_extracted(self, mock_extract):
        mock_extract.return_value = []

        result = await analyze_closet_item(
            image_url="https://example.com/empty.jpg",
            user_tone_id="spring_warm_light",
        )

        assert result["pcf_score"] == 0.0
        assert result["overall_score"] == 0.0
        assert "색상을 추출할 수 없었습니다" in result["reasons"][0]

    @pytest.mark.asyncio
    @patch("app.services.closet_analyzer.extract_colors_from_url")
    @patch("app.services.closet_analyzer._get_palette")
    async def test_overall_score_formula(self, mock_palette, mock_extract):
        mock_extract.return_value = ["#808080"]

        palette_inst = MagicMock()
        palette_inst.match_dominant_colors.return_value = ("summer_cool_mute", "#808080")
        palette_inst.match_color.return_value = ("summer_cool_mute", 10.0)
        palette_inst.tones = {"summer_cool_mute": [(128, 128, 128)]}
        mock_palette.return_value = palette_inst

        with patch("app.services.closet_analyzer._item_pcf", return_value=80.0):
            result = await analyze_closet_item(
                image_url="https://example.com/gray.jpg",
                user_tone_id="summer_cool_mute",
            )

        pcf = result["pcf_score"]
        sat = result["saturation_score"]
        light = result["lightness_score"]
        expected = round(pcf * 0.5 + sat * 0.25 + light * 0.25, 1)
        assert result["overall_score"] == expected

    @pytest.mark.asyncio
    @patch("app.services.closet_analyzer.extract_colors_from_url")
    @patch("app.services.closet_analyzer._get_palette")
    async def test_per_color_tone_matching(self, mock_palette, mock_extract):
        mock_extract.return_value = ["#FF0000", "#0000FF"]

        palette_inst = MagicMock()
        palette_inst.match_dominant_colors.return_value = ("spring_warm_vivid", "#FF0000")
        palette_inst.match_color.side_effect = [
            ("spring_warm_vivid", 10.0),
            ("winter_cool_deep", 15.0),
        ]
        palette_inst.tones = {}
        mock_palette.return_value = palette_inst

        with patch("app.services.closet_analyzer._item_pcf") as mock_pcf:
            mock_pcf.side_effect = [90.0, 40.0]
            result = await analyze_closet_item(
                image_url="https://example.com/two_colors.jpg",
                user_tone_id="spring_warm_vivid",
            )

        assert mock_pcf.call_count == 2
        assert mock_pcf.call_args_list[0][0][0] == "spring_warm_vivid"
        assert mock_pcf.call_args_list[1][0][0] == "winter_cool_deep"
        assert result["pcf_score"] == 65.0

    @pytest.mark.asyncio
    @patch("app.services.closet_analyzer.extract_colors_from_url")
    @patch("app.services.closet_analyzer._get_palette")
    async def test_color_ratios_sum_to_1(self, mock_palette, mock_extract):
        mock_extract.return_value = ["#FF0000", "#00FF00", "#0000FF"]

        palette_inst = MagicMock()
        palette_inst.match_dominant_colors.return_value = ("spring_warm_vivid", "#FF0000")
        palette_inst.match_color.return_value = ("spring_warm_vivid", 10.0)
        palette_inst.tones = {"spring_warm_vivid": [(255, 0, 0)]}
        mock_palette.return_value = palette_inst

        with patch("app.services.closet_analyzer._item_pcf", return_value=70.0):
            result = await analyze_closet_item(
                image_url="https://example.com/rgb.jpg",
                user_tone_id="spring_warm_vivid",
            )

        ratios = [c["ratio"] for c in result["dominant_colors"]]
        assert abs(sum(ratios) - 1.0) < 0.01


# ── Closet API 테스트 ──


class TestClosetApi:
    @patch("app.routers.closet.analyze_closet_item")
    def test_analyze_endpoint(self, mock_analyze):
        from fastapi.testclient import TestClient
        from app.main import app

        mock_analyze.return_value = {
            "dominant_colors": [{"hex": "#F0E0D0", "ratio": 0.5}, {"hex": "#D4A574", "ratio": 0.5}],
            "matched_tone_id": "spring_warm_light",
            "matched_tone_name": "봄 웜 라이트",
            "pcf_score": 88.0,
            "saturation_score": 85.0,
            "lightness_score": 90.0,
            "overall_score": 87.8,
            "reasons": ["봄 웜 라이트 톤과 완벽하게 어울리는 색상이에요."],
        }

        client = TestClient(app)
        resp = client.post("/api/closet/analyze", json={
            "image_url": "https://example.com/shirt.jpg",
            "user_tone_id": "spring_warm_light",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["pcf_score"] == 88.0
        assert data["matched_tone_id"] == "spring_warm_light"

    def test_analyze_missing_fields(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/api/closet/analyze", json={
            "image_url": "https://example.com/shirt.jpg",
        })
        assert resp.status_code == 422

    @patch("app.routers.closet.analyze_closet_item")
    def test_analyze_service_error(self, mock_analyze):
        from fastapi.testclient import TestClient
        from app.main import app

        mock_analyze.side_effect = RuntimeError("네트워크 오류")

        client = TestClient(app)
        resp = client.post("/api/closet/analyze", json={
            "image_url": "https://example.com/broken.jpg",
            "user_tone_id": "spring_warm_light",
        })
        assert resp.status_code == 500

    def test_http_url_rejected(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        resp = client.post("/api/closet/analyze", json={
            "image_url": "http://example.com/shirt.jpg",
            "user_tone_id": "spring_warm_light",
        })
        assert resp.status_code == 422
