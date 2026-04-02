"""A vs B 비교 서비스.

기획서 섹션 6.3 구현.
두 코디를 5축 기준으로 비교하여 결정적 차이 요인을 추출한다.
"""

from __future__ import annotations

from typing import Any

from app.services.feed_builder import DEFAULT_WEIGHTS
from app.services.reason_generator import (
    _load_tone_names,
    _render_template,
    TPO_NAMES_KO,
)

AXIS_NAMES_KO: dict[str, str] = {
    "pcf": "퍼스널컬러 적합도",
    "of": "TPO 적합도",
    "ch": "색상 조화",
    "pe": "가격 효율",
    "sf": "스타일 적합도",
}

AXES = list(DEFAULT_WEIGHTS.keys())


def compare_outfits(
    scores_a: dict[str, float],
    scores_b: dict[str, float],
    tone_id: str | None = None,
    tpo_a: str | None = None,
    tpo_b: str | None = None,
) -> dict[str, Any]:
    """두 코디의 5축 점수를 비교한다.

    Args:
        scores_a: A 코디의 5축 점수
        scores_b: B 코디의 5축 점수
        tone_id: 사용자 톤 ID (이유 생성용)
        tpo_a: A 코디 TPO
        tpo_b: B 코디 TPO

    Returns:
        {
            axis_comparison: [{axis, score_a, score_b, diff, winner}],
            total_a, total_b,
            winner: "A" | "B" | "tie",
            decisive_factor: {axis, axis_name, diff, explanation},
        }
    """
    axis_comparison: list[dict[str, Any]] = []
    diffs_by_axis: dict[str, float] = {}

    for axis in AXES:
        sa = scores_a.get(axis, 0.0)
        sb = scores_b.get(axis, 0.0)
        diff = round(sa - sb, 2)
        winner = "A" if diff > 0 else ("B" if diff < 0 else "tie")
        diffs_by_axis[axis] = diff

        axis_comparison.append({
            "axis": axis,
            "axis_name": AXIS_NAMES_KO.get(axis, axis),
            "score_a": sa,
            "score_b": sb,
            "diff": diff,
            "winner": winner,
        })

    total_a = round(sum(
        scores_a.get(axis, 0.0) * DEFAULT_WEIGHTS[axis] for axis in AXES
    ), 2)
    total_b = round(sum(
        scores_b.get(axis, 0.0) * DEFAULT_WEIGHTS[axis] for axis in AXES
    ), 2)

    if total_a > total_b:
        overall_winner = "A"
    elif total_b > total_a:
        overall_winner = "B"
    else:
        overall_winner = "tie"

    # 결정적 차이 요인: overall winner의 가장 큰 우위 축 선택
    decisive_axis, decisive_diff = _find_decisive_axis(
        diffs_by_axis, overall_winner, scores_a, scores_b,
    )

    decisive_factor = _build_decisive_factor(
        decisive_axis, overall_winner, decisive_diff,
        scores_a, scores_b, tone_id, tpo_a, tpo_b,
    )

    return {
        "axis_comparison": axis_comparison,
        "total_a": total_a,
        "total_b": total_b,
        "winner": overall_winner,
        "decisive_factor": decisive_factor,
    }


def _find_decisive_axis(
    diffs_by_axis: dict[str, float],
    overall_winner: str,
    scores_a: dict[str, float],
    scores_b: dict[str, float],
) -> tuple[str | None, float]:
    """overall winner의 가장 큰 우위 축을 찾는다.

    winner와 decisive_factor.winner가 일치하도록
    winner 방향의 diff만 고려한다. tie인 경우 절대값 최대 축.
    """
    if overall_winner == "tie":
        max_abs = 0.0
        best_axis = None
        for axis, diff in diffs_by_axis.items():
            if abs(diff) > max_abs:
                max_abs = abs(diff)
                best_axis = axis
        return best_axis, max_abs

    best_axis: str | None = None
    best_diff = 0.0
    for axis, diff in diffs_by_axis.items():
        # A가 winner면 diff > 0인 축만, B면 diff < 0인 축만
        if overall_winner == "A" and diff > best_diff:
            best_diff = diff
            best_axis = axis
        elif overall_winner == "B" and diff < -best_diff:
            best_diff = abs(diff)
            best_axis = axis

    return best_axis, best_diff


def _build_decisive_factor(
    axis: str | None,
    winner: str | None,
    diff: float,
    scores_a: dict[str, float],
    scores_b: dict[str, float],
    tone_id: str | None,
    tpo_a: str | None,
    tpo_b: str | None,
) -> dict[str, Any]:
    """결정적 차이 요인을 생성한다."""
    if not axis or diff == 0:
        return {"axis": None, "axis_name": None, "diff": 0.0, "explanation": "두 코디가 동점이에요"}

    axis_name = AXIS_NAMES_KO.get(axis, axis)
    tpo = tpo_a if winner == "A" else tpo_b

    tone_name = None
    if tone_id:
        tone_names = _load_tone_names()
        tone_name = tone_names.get(tone_id)

    # winner 측 실제 점수로 high/mid 분기
    winner_score = scores_a.get(axis, 0.0) if winner == "A" else scores_b.get(axis, 0.0)
    reason = _render_template(axis, winner_score, tone_name, tpo)

    explanation = f"{winner}가 {axis_name}에서 {abs(diff):.0f}점 더 높아요. {reason}"

    return {
        "axis": axis,
        "axis_name": axis_name,
        "diff": round(diff, 2),
        "winner": winner,
        "explanation": explanation,
    }
