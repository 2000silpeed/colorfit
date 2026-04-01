"""Hard Filter 체인: 코디 피드 필터링.

기획서 섹션 5.4 (Hard Filter 상세) 구현.
비용 순서로 적용: H1 → H2 → H3 → H4 → H5 → H7 → H8 → H6
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.scoring import COMPATIBLE_TONES, TPO_SYNONYMS, _expand_tpos
from app.services.style_filter import filter_outfit

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_brand_whitelist: set[str] | None = None


def _load_brand_whitelist() -> set[str]:
    global _brand_whitelist
    if _brand_whitelist is None:
        with open(DATA_DIR / "brand_whitelist.json", encoding="utf-8") as f:
            brands = json.load(f)
        _brand_whitelist = {b.lower() for b in brands}
    return _brand_whitelist


MONTH_TO_SEASON: dict[int, str] = {
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
    12: "winter", 1: "winter", 2: "winter",
}

OPPOSITE_SEASONS: dict[str, str] = {
    "spring": "autumn",
    "summer": "winter",
    "autumn": "spring",
    "winter": "summer",
}


def h1_gender(outfit_gender: str | None, user_gender: str | None) -> bool:
    """H1: 성별 불일치 필터. 통과하면 True."""
    if not user_gender or not outfit_gender:
        return True
    if outfit_gender == "unisex":
        return True
    return outfit_gender == user_gender


def h2_budget(total_price: int | None, budget_max: int | None) -> bool:
    """H2: 예산 초과 필터. 코디 총액 > 예산상한 × 1.5 이면 탈락."""
    if total_price is None or budget_max is None or budget_max <= 0:
        return True
    return total_price <= budget_max * 1.5


def h3_season(
    outfit_season: str | None,
    current_month: int | None = None,
    outfit_tpo: str | None = None,
) -> bool:
    """H3: 계절 완전 불일치 필터. 반대 시즌만 탈락, 인접 시즌 허용."""
    if not outfit_season:
        return True
    if outfit_tpo == "travel":
        return True
    if current_month is None:
        current_month = datetime.now().month
    current_season = MONTH_TO_SEASON.get(current_month)
    if not current_season:
        return True
    return outfit_season != OPPOSITE_SEASONS.get(current_season)


def h4_tpo(
    outfit_tpo: str | None,
    user_tpo_list: list[str] | None,
    active_tab: str | None = None,
) -> bool:
    """H4: TPO 완전 불일치 필터. 동의어 확장 후에도 매칭 0이면 탈락."""
    if active_tab in ("전체", "all"):
        return True
    if not outfit_tpo or not user_tpo_list:
        return True
    expanded = _expand_tpos(user_tpo_list)
    outfit_expanded = TPO_SYNONYMS.get(outfit_tpo, {outfit_tpo})
    return bool(expanded & outfit_expanded)


def h5_brand(item_brands: list[str | None]) -> bool:
    """H5: 브랜드 화이트리스트 필터. 1개 이상 화이트리스트 브랜드면 통과."""
    whitelist = _load_brand_whitelist()
    for brand in item_brands:
        if brand and brand.lower() in whitelist:
            return True
    return False


def h6_llm_quality(llm_quality_score: int | None) -> bool:
    """H6: LLM 품질 필터. 3점 미만 탈락."""
    if llm_quality_score is None:
        return True
    return llm_quality_score >= 3


def h7_tone(
    item_tone_ids: list[str | None],
    user_tone_id: str | None,
) -> bool:
    """H7: 톤 호환성 필터. 매칭 아이템 0개면 탈락."""
    if not user_tone_id:
        return True
    if not item_tone_ids:
        return True
    allowed = {user_tone_id} | COMPATIBLE_TONES.get(user_tone_id, set())
    for tone in item_tone_ids:
        if tone and tone in allowed:
            return True
    return False


def h8_style_filter(items: list[dict]) -> bool:
    """H8: StyleFilter 컷오프 필터. 55점 미만 탈락."""
    passed, _ = filter_outfit(items)
    return passed


def apply_hard_filters(
    outfit: dict[str, Any],
    user: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    current_month: int | None = None,
    active_tab: str | None = None,
) -> tuple[bool, str | None]:
    """Hard Filter 8단계를 순차 적용한다.

    비용이 낮은 순서로 적용: H1 → H2 → H3 → H4 → H5 → H7 → H8 → H6

    Args:
        outfit: 코디 데이터 (gender, designed_tpo, designed_season,
                total_price, llm_quality_score)
        user: 사용자 프로필 (gender, tone_id, tpo_list, budget_max)
        items: 코디 아이템 리스트 (brand, tone_id, category, group, silhouette)
        current_month: 현재 월 (테스트용, None이면 현재 시간 사용)
        active_tab: 피드 탭 ("전체"/"all"이면 H4 비적용)

    Returns:
        (passed, rejection_reason): 통과 여부와 탈락 사유 (통과 시 None)
    """
    if not h1_gender(outfit.get("gender"), user.get("gender")):
        return False, "H1_gender"

    if not h2_budget(outfit.get("total_price"), user.get("budget_max")):
        return False, "H2_budget"

    if not h3_season(
        outfit.get("designed_season"), current_month, outfit.get("designed_tpo"),
    ):
        return False, "H3_season"

    if not h4_tpo(outfit.get("designed_tpo"), user.get("tpo_list"), active_tab):
        return False, "H4_tpo"

    item_brands = [item.get("brand") for item in items]
    if not h5_brand(item_brands):
        return False, "H5_brand"

    item_tones = [item.get("tone_id") for item in items]
    if not h7_tone(item_tones, user.get("tone_id")):
        return False, "H7_tone"

    if not h8_style_filter(items):
        return False, "H8_style_filter"

    if not h6_llm_quality(outfit.get("llm_quality_score")):
        return False, "H6_llm_quality"

    return True, None


# ---------------------------------------------------------------------------
# Soft Score + 리랭킹 (기획서 섹션 6.1, 단계 4-5)
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS: dict[str, float] = {
    "pcf": 0.25,
    "of": 0.20,
    "ch": 0.15,
    "pe": 0.15,
    "sf": 0.25,
}


def calculate_soft_score(
    scores: dict[str, float] | None,
    weight_overrides: dict[str, float] | None = None,
) -> float:
    """프리컴퓨팅된 5축 스코어의 가중합을 계산한다.

    Args:
        scores: 프리컴퓨팅된 5축 점수 (pcf, of, ch, pe, sf)
        weight_overrides: 개인화 가중치 오버라이드

    Returns:
        0~100 범위의 가중합 점수
    """
    if not scores:
        return 0.0
    weights = {**DEFAULT_WEIGHTS, **(weight_overrides or {})}
    total = sum(
        scores.get(axis, 0.0) * weights.get(axis, 0.0)
        for axis in DEFAULT_WEIGHTS
    )
    return round(total, 2)


def rerank(
    scored_outfits: list[dict[str, Any]],
    disliked_ids: set[str] | None = None,
    personalization: dict[str, float] | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """리랭킹 5단계를 순차 적용하여 상위 코디를 반환한다.

    기획서 섹션 6.1 (단계 5) 구현.

    처리 순서:
        1. dislike 제외
        2. 완성도 가산 (상하의+아우터 → +3점)
        3. 개인화 보정 (-10 ~ +10)
        4. 점수순 정렬
        5. 톤 다양성(동일 톤 3개 제한) + 메인아이템 중복 제거(1개 제한)

    Args:
        scored_outfits: 각 dict에 id, soft_score, is_complete_outfit,
                        dominant_tone, main_item_id 키 필요
        disliked_ids: 사용자 dislike 코디 ID 집합
        personalization: 코디 ID → 보정값 매핑 (-10 ~ +10 클램핑)
        limit: 반환 개수 (기본 200)

    Returns:
        리랭킹 적용 후 상위 코디 리스트 (final_score 포함)
    """
    disliked = disliked_ids or set()
    personal = personalization or {}

    candidates = []
    for o in scored_outfits:
        if o.get("id") in disliked:
            continue
        score = o.get("soft_score", 0.0)
        if o.get("is_complete_outfit"):
            score += 3.0
        adj = max(-10.0, min(10.0, personal.get(o["id"], 0.0)))
        score += adj
        candidates.append({**o, "final_score": round(score, 2)})

    candidates.sort(key=lambda o: o["final_score"], reverse=True)

    result: list[dict[str, Any]] = []
    tone_count: dict[str, int] = {}
    main_item_seen: set[str] = set()

    for o in candidates:
        tone = o.get("dominant_tone")
        main_item = o.get("main_item_id")

        if main_item and main_item in main_item_seen:
            continue

        if tone:
            if tone_count.get(tone, 0) >= 3:
                continue
            tone_count[tone] = tone_count.get(tone, 0) + 1

        if main_item:
            main_item_seen.add(main_item)

        result.append(o)

        if len(result) >= limit:
            break

    return result
