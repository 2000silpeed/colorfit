"""SF(Style Fit) 스코어링 테스트.

기획서 섹션 5.5.5 / 6.6 기준.
"""

import pytest

from app.services.scoring import calculate_sf


class TestCalculateSF:
    """SF 스코어링: 카테고리 궁합(50%) + 실루엣 밸런스(25%) + 포멀도 일관성(25%)."""

    def test_blouse_slacks_high_score(self):
        """블라우스+슬랙스+로퍼 → 높은 점수 (궁합 좋음, 포멀도 일치)."""
        score = calculate_sf(
            ["블라우스", "슬랙스", "로퍼"],
            top_silhouette="fitted",
            bottom_silhouette="slim",
        )
        assert score >= 80.0

    def test_hoodie_formal_low_score(self):
        """후드티+슬랙스+더비슈즈 → 카테고리 궁합 낮고 포멀도 편차 있음."""
        score = calculate_sf(
            ["후드티", "슬랙스", "더비슈즈"],
            top_silhouette="oversized",
            bottom_silhouette="slim",
        )
        # 궁합 평균 ~51.7, 실루엣 95, 포멀도 ~61.3 → SF ~71
        assert score < 75.0

    def test_boundary_55(self):
        """경계값 55점 근처 — 부조화 코디가 55점 미만이 되는지 확인."""
        score = calculate_sf(
            ["후드티", "정장바지", "클러치"],
            top_silhouette="oversized",
            bottom_silhouette="slim",
        )
        assert score < 55.0

    def test_perfect_casual_outfit(self):
        """티셔츠+청바지+스니커즈 → 캐주얼 정석, 높은 점수."""
        score = calculate_sf(
            ["티셔츠", "청바지", "스니커즈"],
            top_silhouette="regular",
            bottom_silhouette="regular",
        )
        assert score >= 75.0

    def test_formal_outfit(self):
        """셔츠+슬랙스+더비슈즈 → 비즈니스 정석."""
        score = calculate_sf(
            ["셔츠", "슬랙스", "더비슈즈"],
            top_silhouette="fitted",
            bottom_silhouette="slim",
        )
        assert score >= 85.0

    def test_silhouette_y_line(self):
        """Y라인 (오버사이즈+슬림) → 실루엣 점수 95."""
        score = calculate_sf(
            ["니트", "청바지"],
            top_silhouette="oversized",
            bottom_silhouette="slim",
        )
        assert score >= 80.0

    def test_silhouette_volume_overload(self):
        """오버사이즈+와이드 → 실루엣 점수 60 (볼륨 과다)."""
        score_overload = calculate_sf(
            ["니트", "청바지"],
            top_silhouette="oversized",
            bottom_silhouette="wide",
        )
        score_balanced = calculate_sf(
            ["니트", "청바지"],
            top_silhouette="oversized",
            bottom_silhouette="slim",
        )
        assert score_overload < score_balanced

    def test_formality_mismatch_penalty(self):
        """포멀도 편차 큰 조합 → 포멀도 일관성 점수 낮음."""
        # 레깅스(1) + 블라우스(4) + 힐(5) → std_dev 큰 조합
        score = calculate_sf(["레깅스", "블라우스", "힐"])
        # 레깅스(1), 블라우스(4), 힐(5) → std = 2.08 → 100 - 2.08*40 = 16.7
        assert score < 65.0

    def test_formality_uniform(self):
        """포멀도 일치 → 포멀도 점수 100."""
        score = calculate_sf(
            ["슬랙스", "블라우스", "더비슈즈"],
            top_silhouette="fitted",
            bottom_silhouette="slim",
        )
        assert score >= 85.0

    def test_empty_categories_returns_0(self):
        """빈 카테고리 → 0점."""
        assert calculate_sf([]) == 0.0

    def test_single_item_returns_reasonable(self):
        """단일 아이템 → 기본값 사용."""
        score = calculate_sf(["블라우스"])
        assert 50.0 <= score <= 100.0

    def test_no_silhouette_info(self):
        """실루엣 정보 없이도 카테고리+포멀도로 계산."""
        score = calculate_sf(["블라우스", "슬랙스", "로퍼"])
        assert score >= 70.0

    def test_unknown_category_uses_default(self):
        """알 수 없는 카테고리 → 기본 궁합 60, 포멀도 3."""
        score = calculate_sf(["알수없는카테고리", "블라우스"])
        assert 40.0 <= score <= 80.0

    def test_score_always_in_range(self):
        """모든 결과는 0~100 범위."""
        test_cases = [
            (["블라우스", "슬랙스"], "fitted", "slim"),
            (["후드티", "정장바지"], "oversized", "wide"),
            (["티셔츠"], None, None),
            ([], None, None),
        ]
        for cats, top, bottom in test_cases:
            score = calculate_sf(cats, top, bottom)
            assert 0.0 <= score <= 100.0, f"Score {score} out of range for {cats}"

    def test_onepiece_cardigan_high(self):
        """원피스+가디건+힐 → 궁합 좋지만 포멀도 편차(5,3,5)로 소폭 감점."""
        score = calculate_sf(["원피스", "가디건", "힐"])
        assert score >= 70.0

    def test_crop_high_waist_x_line(self):
        """크롭탑+하이웨이스트 → X라인, 높은 실루엣 점수."""
        score = calculate_sf(
            ["크롭탑", "스커트"],
            top_silhouette="crop",
            bottom_silhouette="high_waist",
        )
        assert score >= 80.0

    def test_formality_pstdev_spec_match(self):
        """포멀도 [4,3] → pstdev=0.5 → 100-0.5*40=80점 (스펙 예시)."""
        from app.services.scoring import _formality_consistency_score

        score = _formality_consistency_score(["슬랙스", "니트"])  # 4, 3
        assert score == pytest.approx(80.0)

    def test_formality_uniform_exact(self):
        """포멀도 전부 동일 → pstdev=0 → 100점."""
        from app.services.scoring import _formality_consistency_score

        score = _formality_consistency_score(["슬랙스", "블라우스", "셔츠"])  # 4,4,4
        assert score == 100.0

    def test_exact_sf_weighted_sum(self):
        """고정 fixture에 대한 가중합 정확 검증."""
        # 블라우스(4)+슬랙스(4) → 궁합 90, 포멀도 pstdev=0 → 100
        # fitted+slim → 실루엣 85
        # SF = 90*0.5 + 85*0.25 + 100*0.25 = 45+21.25+25 = 91.25
        score = calculate_sf(
            ["블라우스", "슬랙스"],
            top_silhouette="fitted",
            bottom_silhouette="slim",
        )
        assert score == pytest.approx(91.25)
