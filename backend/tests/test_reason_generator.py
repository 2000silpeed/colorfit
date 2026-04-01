"""추천 이유 생성 테스트.

기획서 섹션 6.4 기반:
- PCF 최고 기여 시 톤 이름 포함 확인
- OF 최고 기여 시 TPO 한글 이름 확인
- 동점 처리 확인
- high / mid 분기 확인
"""

import pytest

from app.services.reason_generator import (
    _select_top_axes,
    generate_reasons,
)


class TestSelectTopAxes:
    def test_pcf_highest_contribution(self):
        scores = {"pcf": 95, "of": 30, "ch": 40, "pe": 50, "sf": 60}
        top = _select_top_axes(scores)
        assert top[0][0] == "pcf"

    def test_of_highest_contribution(self):
        scores = {"pcf": 20, "of": 100, "ch": 30, "pe": 30, "sf": 20}
        top = _select_top_axes(scores)
        assert top[0][0] == "of"

    def test_returns_two_axes(self):
        scores = {"pcf": 80, "of": 70, "ch": 60, "pe": 50, "sf": 40}
        top = _select_top_axes(scores)
        assert len(top) == 2

    def test_tie_breaking_stable(self):
        """PCF(80*0.25=20)와 SF(80*0.25=20) 동점 시 둘 다 상위 2개에 포함."""
        scores = {"pcf": 80, "of": 50, "ch": 50, "pe": 50, "sf": 80}
        top = _select_top_axes(scores)
        axes = {t[0] for t in top}
        assert "pcf" in axes
        assert "sf" in axes


class TestGenerateReasons:
    def test_pcf_high_includes_tone_name(self):
        scores = {"pcf": 90, "of": 30, "ch": 40, "pe": 50, "sf": 60}
        reasons = generate_reasons(
            scores, user_tone_id="summer_cool_soft", outfit_tpo="date",
        )
        assert len(reasons) == 2
        assert "여름 쿨 소프트" in reasons[0]
        assert "밝아 보여요" in reasons[0]

    def test_of_high_includes_tpo_name(self):
        scores = {"pcf": 20, "of": 95, "ch": 30, "pe": 30, "sf": 20}
        reasons = generate_reasons(
            scores, user_tone_id="spring_warm_light", outfit_tpo="date",
        )
        assert "데이트" in reasons[0]
        assert "적합한" in reasons[0]

    def test_pcf_mid_template(self):
        scores = {"pcf": 60, "of": 20, "ch": 20, "pe": 20, "sf": 50}
        reasons = generate_reasons(scores, user_tone_id="summer_cool_soft")
        pcf_reason = reasons[0]
        assert "비교적" in pcf_reason

    def test_of_mid_template(self):
        scores = {"pcf": 20, "of": 60, "ch": 20, "pe": 20, "sf": 20}
        reasons = generate_reasons(scores, outfit_tpo="date")
        of_reason = reasons[0]
        assert "무난하게" in of_reason

    def test_ch_high_template(self):
        scores = {"pcf": 10, "of": 10, "ch": 95, "pe": 10, "sf": 10}
        reasons = generate_reasons(scores)
        assert "조화" in reasons[0]

    def test_pe_high_template(self):
        scores = {"pcf": 10, "of": 10, "ch": 10, "pe": 95, "sf": 10}
        reasons = generate_reasons(scores)
        assert "가성비" in reasons[0]

    def test_sf_high_template(self):
        scores = {"pcf": 10, "of": 10, "ch": 10, "pe": 10, "sf": 95}
        reasons = generate_reasons(scores)
        assert "스타일 조화" in reasons[0]

    def test_empty_scores(self):
        assert generate_reasons({}) == []

    def test_no_tone_id_fallback(self):
        """톤 ID 없이 PCF high 시 '퍼스널컬러'로 대체."""
        scores = {"pcf": 90, "of": 30, "ch": 30, "pe": 30, "sf": 30}
        reasons = generate_reasons(scores)
        assert "퍼스널컬러" in reasons[0]

    def test_unknown_tpo_uses_raw(self):
        """알 수 없는 TPO는 원본 문자열 사용."""
        scores = {"pcf": 20, "of": 95, "ch": 30, "pe": 30, "sf": 20}
        reasons = generate_reasons(scores, outfit_tpo="custom_event")
        assert "custom_event" in reasons[0]

    def test_boundary_75_high(self):
        """75점 정확히 high 분기."""
        scores = {"pcf": 75, "of": 10, "ch": 10, "pe": 10, "sf": 10}
        reasons = generate_reasons(
            scores, user_tone_id="summer_cool_soft",
        )
        assert "밝아 보여요" in reasons[0]

    def test_boundary_74_mid(self):
        """74점은 mid 분기."""
        scores = {"pcf": 74, "of": 10, "ch": 10, "pe": 10, "sf": 10}
        reasons = generate_reasons(
            scores, user_tone_id="summer_cool_soft",
        )
        assert "비교적" in reasons[0]
