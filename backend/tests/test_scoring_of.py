"""OF(Occasion Fit) 스코어링 테스트.

기획서 섹션 5.5.2 기준.
"""

import pytest

from app.services.scoring import TPO_SYNONYMS, _expand_tpos, calculate_of


class TestExpandTpos:
    def test_single_tpo_with_synonyms(self):
        result = _expand_tpos(["commute"])
        assert result == {"office", "commute"}

    def test_single_tpo_no_synonyms(self):
        result = _expand_tpos(["workout"])
        assert result == {"workout"}

    def test_multiple_tpos(self):
        result = _expand_tpos(["commute", "weekend"])
        assert result == {"office", "commute", "casual", "weekend", "daily"}

    def test_unknown_tpo_passes_through(self):
        result = _expand_tpos(["unknown_tpo"])
        assert result == {"unknown_tpo"}

    def test_empty_list(self):
        result = _expand_tpos([])
        assert result == set()

    def test_interview_expands_to_office(self):
        """interview → {interview, office} (단방향 확장)"""
        result = _expand_tpos(["interview"])
        assert result == {"interview", "office"}
        # office → {office, commute} — interview 포함 안 됨
        result_office = _expand_tpos(["office"])
        assert "interview" not in result_office


class TestCalculateOf:
    def test_exact_match_single(self):
        """정확 매칭: best_sim=1.0 → 30+70=100"""
        score = calculate_of(["office"], ["office"])
        assert score == 100.0

    def test_exact_match_multiple(self):
        """정확 매칭 2개: best_sim=1.0 → 100"""
        score = calculate_of(["office", "casual"], ["office", "casual"])
        assert score == 100.0

    def test_synonym_match(self):
        """유사 TPO: commute↔office sim=0.9 → 30+63=93"""
        score = calculate_of(["office"], ["commute"])
        assert score == 93.0

    def test_synonym_match_weekend_casual(self):
        """weekend↔casual sim=0.9 → 93"""
        score = calculate_of(["casual", "daily"], ["weekend"])
        assert score == 93.0

    def test_no_match(self):
        """완전 미매칭: 30점 하한"""
        score = calculate_of(["workout"], ["date"])
        assert score == 30.0

    def test_partial_match_with_extra_tags(self):
        """3개 태그 중 office 정확 매칭: best_sim=1.0 → 100"""
        score = calculate_of(["office", "workout", "travel"], ["office"])
        assert score == 100.0

    def test_partial_match_2_of_4(self):
        """office↔commute sim=0.9 → 93"""
        score = calculate_of(
            ["office", "casual", "workout", "travel"],
            ["commute"],
        )
        assert score == 93.0

    def test_empty_outfit_tags(self):
        score = calculate_of([], ["office"])
        assert score == 30.0

    def test_empty_user_tpo(self):
        score = calculate_of(["office"], [])
        assert score == 30.0

    def test_both_empty(self):
        score = calculate_of([], [])
        assert score == 30.0

    def test_score_never_below_30(self):
        """어떤 입력이든 30점 미만이 되지 않는다"""
        score = calculate_of(["workout"], ["interview"])
        assert score >= 30.0

    def test_score_never_above_100(self):
        """점수가 100을 넘지 않는다"""
        score = calculate_of(
            ["office", "commute", "casual"],
            ["office", "commute", "casual", "weekend", "daily"],
        )
        assert score <= 100.0

    def test_interview_matches_office_tag(self):
        """interview↔office sim=0.8 → 30+56=86"""
        score = calculate_of(["office", "casual"], ["interview"])
        assert score == 86.0

    def test_campus_matches_casual(self):
        """campus↔casual sim=0.8 → 30+56=86"""
        score = calculate_of(["casual", "daily"], ["campus"])
        assert score == 86.0
