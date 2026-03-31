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
        """정확 매칭 1개: 60 + (1/total_tags) * 20"""
        score = calculate_of(["office"], ["office"])
        assert score == 80.0  # 60 + (1/1)*20

    def test_exact_match_multiple(self):
        """정확 매칭 2개 이상: 80 + (match/total)*20"""
        score = calculate_of(["office", "casual"], ["office", "casual"])
        assert score == 100.0  # 80 + (2/2)*20

    def test_synonym_match(self):
        """동의어 매칭: commute 사용자 → office 태그 코디 매칭"""
        score = calculate_of(["office"], ["commute"])
        assert score == 80.0  # office는 commute의 동의어

    def test_synonym_match_weekend_casual(self):
        """weekend ↔ casual 동의어"""
        score = calculate_of(["casual", "daily"], ["weekend"])
        assert score >= 80.0  # casual, daily 둘 다 weekend 동의어

    def test_no_match(self):
        """완전 미매칭: 30점 하한"""
        score = calculate_of(["workout"], ["date"])
        assert score == 30.0

    def test_partial_match_with_extra_tags(self):
        """3개 태그 중 1개 매칭"""
        score = calculate_of(["office", "workout", "travel"], ["office"])
        # match_count=1, total_tags=3: 60 + (1/3)*20 ≈ 66.67
        assert score == pytest.approx(66.67, abs=0.01)

    def test_partial_match_2_of_4(self):
        """4개 태그 중 2개 매칭"""
        score = calculate_of(
            ["office", "casual", "workout", "travel"],
            ["commute"],  # → {office, commute}
        )
        # match_count=1 (office만 매칭), total_tags=4: 60 + (1/4)*20 = 65
        assert score == 65.0

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
        """면접 사용자에게 office 태그 코디 매칭"""
        score = calculate_of(["office", "casual"], ["interview"])
        # interview → {interview, office}, office 매칭 → match_count=1
        # 60 + (1/2)*20 = 70
        assert score == 70.0

    def test_campus_matches_casual(self):
        """campus → {campus, casual} 확장"""
        score = calculate_of(["casual", "daily"], ["campus"])
        # campus → {campus, casual}, casual 매칭 → match_count=1
        # 60 + (1/2)*20 = 70
        assert score == 70.0
