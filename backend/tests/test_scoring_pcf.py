"""PCF 스코어링 테스트.

기획서 5.5.1 기반: 동일 톤, 호환 톤, 반대 시즌, 경계값.
scoring 함수는 순수 함수이므로 mock 없이 직접 테스트한다.
"""

import pytest

from app.services.scoring import (
    COMPATIBLE_TONES,
    _DISTANCE_DIVISOR,
    _item_pcf,
    calculate_pcf,
)
from app.services.color_matcher import TonePalette


@pytest.fixture(scope="module")
def palette() -> TonePalette:
    return TonePalette()


class TestCompatibleTones:
    """호환 톤 매트릭스가 올바른지 확인."""

    def test_all_13_tones_defined(self):
        assert len(COMPATIBLE_TONES) == 13

    def test_same_season_only(self):
        for tone_id, compat_set in COMPATIBLE_TONES.items():
            season = tone_id.split("_")[0]
            for compat in compat_set:
                assert compat.startswith(season), (
                    f"{tone_id}의 호환 톤 {compat}가 다른 시즌"
                )

    def test_no_self_reference(self):
        for tone_id, compat_set in COMPATIBLE_TONES.items():
            assert tone_id not in compat_set

    def test_symmetry(self):
        """A가 B의 호환이면 B도 A의 호환이어야 한다."""
        for tone_id, compat_set in COMPATIBLE_TONES.items():
            for compat in compat_set:
                assert tone_id in COMPATIBLE_TONES[compat], (
                    f"{tone_id} → {compat} 호환이지만 역방향 없음"
                )

    def test_within_season_completeness(self):
        """같은 시즌 내 모든 다른 톤이 호환 톤에 포함되어야 한다."""
        by_season: dict[str, list[str]] = {}
        for tone_id in COMPATIBLE_TONES:
            season = tone_id.split("_")[0]
            by_season.setdefault(season, []).append(tone_id)
        for season, tones in by_season.items():
            for tone_id in tones:
                expected = {t for t in tones if t != tone_id}
                assert COMPATIBLE_TONES[tone_id] == expected, (
                    f"{tone_id}: 호환 톤 누락 {expected - COMPATIBLE_TONES[tone_id]}"
                )


class TestDistanceDivisor:
    """기획서 명시값 4.42 사용 확인."""

    def test_divisor_matches_spec(self):
        assert _DISTANCE_DIVISOR == 4.42


class TestItemPcf:
    """단일 아이템 PCF 점수 테스트."""

    def test_same_tone_100(self, palette):
        score = _item_pcf(
            "spring_warm_light", "#FADADD", "spring_warm_light", palette
        )
        assert score == 100.0

    def test_compatible_tone_95(self, palette):
        score = _item_pcf(
            "spring_warm_bright", "#FF6B6B", "spring_warm_light", palette
        )
        assert score == 95.0

    def test_opposite_season_lower(self, palette):
        score = _item_pcf(
            "winter_cool_deep", "#1A1A2E", "spring_warm_light", palette
        )
        assert score < 80.0

    def test_color_distance_score_range(self, palette):
        score = _item_pcf(
            "autumn_warm_deep", "#5C3A21", "spring_warm_light", palette
        )
        assert 0.0 <= score <= 100.0

    def test_identical_hex_high_score(self, palette):
        score = _item_pcf(
            "autumn_warm_deep", "#FADADD", "spring_warm_light", palette
        )
        assert score >= 80.0

    def test_exact_formula(self, palette):
        """d_min=4일 때 기획서 공식 score = 100 - 4/4.42 = 99.0950... 확인."""
        d_min = 4.0
        expected = 100.0 - (d_min / 4.42)
        assert abs(expected - 99.09502262443439) < 1e-6


class TestCalculatePcf:
    """코디 전체 PCF 점수 테스트."""

    def test_all_same_tone_100(self, palette):
        score = calculate_pcf(
            item_tone_ids=["spring_warm_light", "spring_warm_light"],
            item_hex_colors=["#FADADD", "#FFE4C4"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert score == 100.0

    def test_all_compatible_95(self, palette):
        score = calculate_pcf(
            item_tone_ids=["spring_warm_bright", "spring_warm_vivid"],
            item_hex_colors=["#FF6B6B", "#FF4500"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert score == 95.0

    def test_mixed_same_and_compatible(self, palette):
        score = calculate_pcf(
            item_tone_ids=["spring_warm_light", "spring_warm_bright"],
            item_hex_colors=["#FADADD", "#FF6B6B"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert score == 97.5  # (100 + 95) / 2

    def test_opposite_season_low(self, palette):
        score = calculate_pcf(
            item_tone_ids=["winter_cool_deep", "winter_cool_strong"],
            item_hex_colors=["#1A1A2E", "#0F0F23"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert score < 70.0

    def test_empty_returns_zero(self, palette):
        assert calculate_pcf([], [], "spring_warm_light", palette) == 0.0

    def test_mismatched_lengths_raises(self, palette):
        with pytest.raises(ValueError, match="길이가 다릅니다"):
            calculate_pcf(
                item_tone_ids=["spring_warm_light"],
                item_hex_colors=["#FADADD", "#FFE4C4"],
                user_tone_id="spring_warm_light",
                palette=palette,
            )

    def test_partial_empty_ids_raises(self, palette):
        """[P1 fix] 한쪽만 빈 리스트면 ValueError."""
        with pytest.raises(ValueError, match="길이가 다릅니다"):
            calculate_pcf(
                item_tone_ids=[],
                item_hex_colors=["#FFFFFF"],
                user_tone_id="spring_warm_light",
                palette=palette,
            )

    def test_partial_empty_colors_raises(self, palette):
        """[P1 fix] 한쪽만 빈 리스트면 ValueError."""
        with pytest.raises(ValueError, match="길이가 다릅니다"):
            calculate_pcf(
                item_tone_ids=["spring_warm_light"],
                item_hex_colors=[],
                user_tone_id="spring_warm_light",
                palette=palette,
            )

    def test_single_item(self, palette):
        score = calculate_pcf(
            item_tone_ids=["spring_warm_light"],
            item_hex_colors=["#FADADD"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert score == 100.0

    def test_score_bounded_0_100(self, palette):
        score = calculate_pcf(
            item_tone_ids=["winter_cool_deep"],
            item_hex_colors=["#000000"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert 0.0 <= score <= 100.0

    def test_black_against_warm_tone(self, palette):
        score = calculate_pcf(
            item_tone_ids=["winter_cool_deep"],
            item_hex_colors=["#000000"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert score < 60.0

    def test_white_moderate_score(self, palette):
        score = calculate_pcf(
            item_tone_ids=["summer_cool_light"],
            item_hex_colors=["#FFFFFF"],
            user_tone_id="spring_warm_light",
            palette=palette,
        )
        assert 50.0 <= score <= 100.0
