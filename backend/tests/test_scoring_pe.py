"""PE(Price Efficiency) 스코어링 테스트.

기획서 섹션 5.5.4 기준.
"""

import pytest

from app.services.scoring import calculate_pe


class TestCalculatePE:
    """예산 범위: 50_000 ~ 150_000 (중앙: 100_000)으로 테스트."""

    BUDGET_MIN = 50_000
    BUDGET_MAX = 150_000

    def test_exact_mid_returns_100(self):
        """예산 정중앙 → 100점."""
        score = calculate_pe(100_000, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == 100.0

    def test_at_budget_max(self):
        """예산 상한 → 100 - |150000-100000|/100000 * 30 = 85점."""
        score = calculate_pe(150_000, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == pytest.approx(85.0)

    def test_at_budget_min(self):
        """예산 하한 → 100 - |50000-100000|/100000 * 30 = 85점."""
        score = calculate_pe(50_000, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == pytest.approx(85.0)

    def test_within_range_near_mid(self):
        """범위 내 중앙 근처 → 높은 점수."""
        score = calculate_pe(110_000, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score > 90.0

    def test_over_10_percent(self):
        """10% 초과 → 70 - 0.1*100 = 60점."""
        over_price = self.BUDGET_MAX * 1.1  # 165_000
        score = calculate_pe(over_price, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == pytest.approx(60.0)

    def test_over_50_percent(self):
        """50% 초과 → 70 - 0.5*100 = 20점."""
        over_price = self.BUDGET_MAX * 1.5  # 225_000
        score = calculate_pe(over_price, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == pytest.approx(20.0)

    def test_over_70_percent_returns_0(self):
        """70% 초과 → 0점."""
        over_price = self.BUDGET_MAX * 1.7  # 255_000
        score = calculate_pe(over_price, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == 0.0

    def test_under_budget_mild(self):
        """예산 미만 완만 감점."""
        score = calculate_pe(40_000, self.BUDGET_MIN, self.BUDGET_MAX)
        assert 40.0 <= score < 80.0

    def test_extreme_low_price_floors_at_40(self):
        """극단 저가 → 최저 40점."""
        score = calculate_pe(1_000, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == 40.0

    def test_zero_price_floors_at_40(self):
        """가격 0원 → 최저 40점."""
        score = calculate_pe(0, self.BUDGET_MIN, self.BUDGET_MAX)
        assert score == 40.0

    def test_score_always_in_range(self):
        """모든 결과는 0~100 범위."""
        test_prices = [0, 1_000, 30_000, 50_000, 100_000, 150_000, 200_000, 500_000]
        for price in test_prices:
            score = calculate_pe(price, self.BUDGET_MIN, self.BUDGET_MAX)
            assert 0.0 <= score <= 100.0, f"Score {score} out of range for price {price}"

    def test_invalid_budget_returns_0(self):
        """잘못된 예산 범위 → 0점."""
        assert calculate_pe(100_000, 0, 100_000) == 0.0
        assert calculate_pe(100_000, -1, 100_000) == 0.0
        assert calculate_pe(100_000, 200_000, 100_000) == 0.0
