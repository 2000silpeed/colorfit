"""내 아이템 기반 코디 매칭 서비스 (F-57 전략 A).

옷장 아이템의 색상/카테고리를 기반으로 DB 코디에서
유사 아이템을 포함한 코디를 탐색하고, 5축 스코어를 재계산한다.
기획서 F-57 상세 설계 참조.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.color_matcher import _hex_to_rgb, _rgb_distance
from app.services.feed_builder import (
    MONTH_TO_SEASON,
    OPPOSITE_SEASONS,
    calculate_soft_score,
)
from app.services.feed_service import (
    _load_feed_cache,
    category_to_group,
)
from app.services.reason_generator import generate_reasons
from app.services.scoring import (
    calculate_ch,
    calculate_pcf,
    calculate_pe,
)

RGB_DISTANCE_THRESHOLD = 60.0


def _exclude_first_match(items: list[dict], target_id: str) -> list[dict]:
    """items에서 target_id와 일치하는 첫 번째 아이템만 제외한다."""
    result = []
    found = False
    for it in items:
        if not found and it["id"] == target_id:
            found = True
            continue
        result.append(it)
    return result


def _find_matching_slot(
    my_item_group: str,
    my_item_color_hex: str,
    outfit_items: list[dict],
) -> dict | None:
    """코디 아이템 중 내 아이템과 같은 카테고리 그룹 + 유사 색상(RGB < 60)인 것을 찾는다."""
    if not my_item_color_hex:
        return None

    my_rgb = _hex_to_rgb(my_item_color_hex)
    best: dict | None = None
    best_dist = RGB_DISTANCE_THRESHOLD

    for item in outfit_items:
        if item.get("group") != my_item_group:
            continue
        item_hex = item.get("color_hex")
        if not item_hex:
            continue
        dist = _rgb_distance(my_rgb, _hex_to_rgb(item_hex))
        if dist < best_dist:
            best_dist = dist
            best = item

    return best


def _apply_hard_filters(
    outfit: SimpleNamespace,
    gender: str | None,
    age_group: str | None,
) -> bool:
    """성별/연령대/반대 시즌 Hard Filter."""
    if gender:
        if not (outfit.gender == gender or outfit.gender == "unisex" or outfit.gender is None):
            return False
    if age_group:
        if not (outfit.age_group == age_group or outfit.age_group is None):
            return False

    current_month = datetime.now().month
    current_season = MONTH_TO_SEASON.get(current_month)
    opposite = OPPOSITE_SEASONS.get(current_season) if current_season else None
    if opposite:
        if outfit.designed_season == opposite and outfit.designed_season is not None:
            if outfit.designed_tpo != "travel":
                return False

    return True


def _recalculate_scores(
    outfit: SimpleNamespace,
    outfit_items: list[dict],
    matched_slot: dict,
    my_item: dict,
    user_tone_id: str,
    budget_max: int | None,
) -> dict[str, float]:
    """내 아이템을 반영하여 5축 스코어를 재계산한다.

    - PCF: 내 아이템 실측 PCF + 나머지 아이템 PCF 평균
    - OF: 기존 OF 유지 (코디 단위 TPO)
    - CH: 내 아이템 색상 포함 재계산
    - PE: 추가 구매 비용 기준 재계산
    - SF: 기존 SF 유지 (카테고리 궁합 변동 없음)
    """
    existing_scores = outfit.scores or {}

    other_items = _exclude_first_match(outfit_items, matched_slot["id"])

    # PCF 재계산: 내 아이템 실측 + 나머지 평균
    all_tone_ids: list[str] = []
    all_hex_colors: list[str] = []
    for it in other_items:
        if it.get("tone_id") and it.get("color_hex"):
            all_tone_ids.append(it["tone_id"])
            all_hex_colors.append(it["color_hex"])
    if my_item.get("matched_tone_id") and my_item.get("dominant_color_hex"):
        all_tone_ids.append(my_item["matched_tone_id"])
        all_hex_colors.append(my_item["dominant_color_hex"])

    pcf = calculate_pcf(all_tone_ids, all_hex_colors, user_tone_id) if all_tone_ids else 0.0

    # OF: 기존 유지
    of_score = existing_scores.get("of", 50.0)

    # CH 재계산: 내 아이템 색상 포함
    ch_hex_colors: list[str] = []
    for it in other_items:
        if it.get("color_hex"):
            ch_hex_colors.append(it["color_hex"])
    if my_item.get("dominant_color_hex"):
        ch_hex_colors.append(my_item["dominant_color_hex"])
    ch = calculate_ch(ch_hex_colors) if len(ch_hex_colors) >= 2 else 50.0

    # PE 재계산: 추가 구매 비용 기준 (0원이면 추가 구매 불필요 → 만점)
    purchase_cost = sum(it.get("price") or 0 for it in other_items)
    if purchase_cost == 0:
        pe = 100.0
    elif budget_max and budget_max > 0:
        pe = calculate_pe(purchase_cost, 1, budget_max)
    else:
        pe = existing_scores.get("pe", 50.0)

    # SF: 기존 유지
    sf = existing_scores.get("sf", 50.0)

    return {
        "pcf": pcf,
        "of": of_score,
        "ch": ch,
        "pe": pe,
        "sf": sf,
    }


def _build_outfit_result(
    outfit: SimpleNamespace,
    outfit_items: list[dict],
    matched_slot: dict,
    my_item: dict,
    scores: dict[str, float],
    total_score: float,
    user_tone_id: str,
) -> dict:
    """코디 매칭 결과를 API 응답 형식으로 조립한다."""
    other_items = _exclude_first_match(outfit_items, matched_slot["id"])
    purchase_total = sum(it.get("price") or 0 for it in other_items)

    reasons = generate_reasons(
        scores=scores,
        user_tone_id=user_tone_id,
        outfit_tpo=outfit.designed_tpo,
        outfit_id=outfit.id,
    )

    result_items = [
        {
            "id": str(my_item["id"]),
            "source": "closet",
            "category": my_item.get("category"),
            "image_url": my_item.get("image_url"),
            "label": "내 옷",
        }
    ]
    for it in other_items:
        result_items.append({
            "id": it["id"],
            "source": "catalog",
            "category": it.get("category"),
            "image_url": it.get("image_url"),
            "name": None,
            "brand": it.get("brand"),
            "price": it.get("price"),
            "mall_url": None,
        })

    return {
        "id": str(uuid.uuid4()),
        "source": "db_match",
        "db_outfit_id": outfit.id,
        "total_score": total_score,
        "scores": scores,
        "reasons": reasons,
        "items": result_items,
        "purchase_summary": {
            "my_items_count": 1,
            "purchase_items_count": len(other_items),
            "purchase_total": purchase_total,
        },
    }


async def match_outfits_for_closet_item(
    db: AsyncSession,
    *,
    closet_item_id: str,
    user_id: str,
    user_tone_id: str,
    gender: str | None = None,
    age_group: str | None = None,
    tpo: str | None = None,
    budget_max: int | None = None,
    limit: int = 10,
) -> dict:
    """DB 코디에서 내 아이템과 매칭되는 코디를 탐색한다.

    Returns:
        {outfits: [...], total_count: int, strategy_used: str}
    """
    from sqlalchemy import text as sa_text

    row = (await db.execute(
        sa_text(
            "SELECT id, category, dominant_color_hex, matched_tone_id, image_url "
            "FROM closet_items WHERE id = :cid AND user_id = :uid"
        ),
        {"cid": closet_item_id, "uid": user_id},
    )).mappings().first()
    if not row:
        return {"outfits": [], "total_count": 0, "strategy_used": "db_match"}

    my_item = {
        "id": row["id"],
        "category": row["category"],
        "dominant_color_hex": row["dominant_color_hex"],
        "matched_tone_id": row["matched_tone_id"],
        "image_url": row["image_url"],
    }
    raw_category = my_item.get("category") or ""
    my_group = category_to_group(raw_category) or raw_category

    if not my_group or not my_item.get("dominant_color_hex"):
        return {"outfits": [], "total_count": 0, "strategy_used": "db_match"}

    outfits, item_map = await _load_feed_cache(db)

    # TPO 필터 (선택)
    tpo_set: set[str] | None = None
    if tpo:
        from app.services.scoring import TPO_SYNONYMS
        tpo_set = TPO_SYNONYMS.get(tpo, {tpo})

    candidates: list[dict] = []

    for outfit in outfits:
        if not _apply_hard_filters(outfit, gender, age_group):
            continue

        if tpo_set is not None:
            if not (outfit.designed_tpo in tpo_set or outfit.designed_tpo is None):
                continue

        outfit_items = item_map.get(outfit.id, [])
        if not outfit_items:
            continue

        matched_slot = _find_matching_slot(my_group, my_item["dominant_color_hex"], outfit_items)
        if matched_slot is None:
            continue

        scores = _recalculate_scores(
            outfit, outfit_items, matched_slot, my_item, user_tone_id, budget_max,
        )
        total_score = calculate_soft_score(scores)

        candidates.append({
            "outfit": outfit,
            "outfit_items": outfit_items,
            "matched_slot": matched_slot,
            "scores": scores,
            "total_score": total_score,
        })

    candidates.sort(key=lambda c: c["total_score"], reverse=True)
    top = candidates[:min(limit, 10)]

    results = [
        _build_outfit_result(
            c["outfit"],
            c["outfit_items"],
            c["matched_slot"],
            my_item,
            c["scores"],
            c["total_score"],
            user_tone_id,
        )
        for c in top
    ]

    return {
        "outfits": results,
        "total_count": len(results),
        "strategy_used": "db_match",
    }
