"""evaluate_outfits.py 유닛 테스트.

검증 대상: 프롬프트 생성, 점수 파싱, 저품질 필터링.
Gemini API 호출은 mock 처리.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.evaluate_outfits import (
    build_prompt,
    filter_low_quality,
    format_items_text,
    parse_score,
)


def _outfit(
    outfit_id: str = "outfit_f_springwa_date_sp_001",
    gender: str = "female",
    tpo: str = "date",
    season: str = "spring",
    moods: list[str] | None = None,
    score: int | None = None,
) -> dict:
    return {
        "id": outfit_id,
        "gender": gender,
        "designed_tpo": tpo,
        "designed_season": season,
        "designed_moods": moods or ["lovely", "casual"],
        "items_snapshot": [
            {
                "product_id": "p1",
                "name": "플라워 블라우스",
                "category": "블라우스",
                "price": 35000,
                "formality": 4,
            },
            {
                "product_id": "p2",
                "name": "A라인 스커트",
                "category": "스커트",
                "price": 42000,
                "formality": 3,
            },
        ],
        "llm_quality_score": score,
    }


class TestParseScore:
    def test_valid_json(self):
        score, reason = parse_score('{"score": 4, "reason": "잘 어울림"}')
        assert score == 4
        assert reason == "잘 어울림"

    def test_json_with_code_block(self):
        score, reason = parse_score('```json\n{"score": 3, "reason": "보통"}\n```')
        assert score == 3

    def test_score_boundary_1(self):
        score, _ = parse_score('{"score": 1, "reason": "별로"}')
        assert score == 1

    def test_score_boundary_5(self):
        score, _ = parse_score('{"score": 5, "reason": "완벽"}')
        assert score == 5

    def test_score_out_of_range_0(self):
        score, _ = parse_score('{"score": 0, "reason": "invalid"}')
        assert score is None

    def test_score_out_of_range_6(self):
        score, _ = parse_score('{"score": 6, "reason": "invalid"}')
        assert score is None

    def test_malformed_json_with_score(self):
        score, _ = parse_score('blah blah "score": 4 blah')
        assert score == 4

    def test_completely_invalid(self):
        score, _ = parse_score("이건 JSON이 아닙니다")
        assert score is None

    def test_empty_string(self):
        score, _ = parse_score("")
        assert score is None

    def test_missing_reason(self):
        score, reason = parse_score('{"score": 3}')
        assert score == 3
        assert reason == ""


class TestFormatItemsText:
    def test_basic(self):
        items = [
            {"product_id": "1", "name": "셔츠", "category": "셔츠", "price": 30000, "formality": 4},
        ]
        text = format_items_text(items)
        assert "셔츠" in text
        assert "30,000원" in text
        assert "포멀도 4" in text

    def test_zero_price(self):
        items = [
            {"product_id": "1", "name": "테스트", "category": "니트", "price": 0, "formality": 3},
        ]
        text = format_items_text(items)
        assert "가격 미상" in text


class TestBuildPrompt:
    def test_contains_outfit_info(self):
        outfit = _outfit()
        prompt = build_prompt(outfit)
        assert "여성" in prompt
        assert "date" in prompt
        assert "봄" in prompt
        assert "lovely" in prompt
        assert "블라우스" in prompt
        assert "스커트" in prompt

    def test_male_winter_prompt(self):
        outfit = _outfit(gender="male", season="winter")
        prompt = build_prompt(outfit)
        assert "남성" in prompt
        assert "겨울" in prompt


class TestFilterLowQuality:
    def test_filter_below_3(self):
        outfits = [
            _outfit("a", score=5),
            _outfit("b", score=2),
            _outfit("c", score=3),
            _outfit("d", score=1),
        ]
        passed, removed = filter_low_quality(outfits, min_score=3)
        assert len(passed) == 2
        assert len(removed) == 2
        assert all(o["llm_quality_score"] >= 3 for o in passed)
        assert all(o["llm_quality_score"] < 3 for o in removed)

    def test_unscored_kept(self):
        outfits = [_outfit("a", score=None), _outfit("b", score=4)]
        passed, removed = filter_low_quality(outfits)
        assert len(passed) == 2
        assert len(removed) == 0

    def test_all_pass(self):
        outfits = [_outfit("a", score=4), _outfit("b", score=5)]
        passed, removed = filter_low_quality(outfits)
        assert len(passed) == 2
        assert len(removed) == 0

    def test_all_fail(self):
        outfits = [_outfit("a", score=1), _outfit("b", score=2)]
        passed, removed = filter_low_quality(outfits)
        assert len(passed) == 0
        assert len(removed) == 2
