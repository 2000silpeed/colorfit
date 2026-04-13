"""내 아이템 기반 코디 매칭 서비스 (F-57 전략 A + B).

전략 A: 옷장 아이템의 색상/카테고리를 기반으로 DB 코디에서
유사 아이템을 포함한 코디를 탐색하고, 5축 스코어를 재계산한다.

전략 B (Fallback): DB 매칭 결과 < 3개일 때, 개별 상품을 조합하여
동적 코디를 생성한다. 복수 아이템 입력도 지원.

기획서 F-57 상세 설계 참조.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from types import SimpleNamespace

import itertools

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.services.color_matcher import _hex_to_rgb, _rgb_distance
from app.services.closet_recommender import COMPLEMENTARY_CATEGORIES
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
    COMPATIBLE_TONES,
    calculate_ch,
    calculate_pcf,
    calculate_pe,
)

RGB_DISTANCE_THRESHOLD = 60.0

FULL_OUTFIT_SLOTS: dict[str, list[str]] = {
    "top": ["bottom", "shoes"],
    "bottom": ["top", "shoes"],
    "outer": ["top", "bottom", "shoes"],
    "onepiece": ["shoes", "bag"],
    "shoes": ["top", "bottom"],
    "bag": ["top", "bottom", "shoes"],
    "acc": ["top", "bottom", "shoes"],
}

OPTIONAL_SLOTS: dict[str, list[str]] = {
    "top": ["outer", "bag", "acc"],
    "bottom": ["outer", "bag", "acc"],
    "outer": ["bag", "acc"],
    "onepiece": ["outer", "acc"],
    "shoes": ["outer", "bag", "acc"],
    "bag": ["outer", "acc"],
    "acc": ["bag"],
}

DYNAMIC_COMBO_LIMIT = 5
SLOT_CANDIDATE_LIMIT = 8


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


def _determine_needed_slots(
    my_groups: list[str],
) -> tuple[list[str], list[str]]:
    """보유 그룹에서 필수/선택 슬롯을 결정한다.

    복수 아이템이면 이미 보유한 슬롯을 제외하고 나머지를 반환한다.
    """
    if not my_groups:
        return [], []

    primary = my_groups[0]
    required = list(FULL_OUTFIT_SLOTS.get(primary, ["top", "bottom", "shoes"]))
    optional = list(OPTIONAL_SLOTS.get(primary, []))

    owned = set(my_groups)
    required = [s for s in required if s not in owned]
    optional = [s for s in optional if s not in owned and s not in set(required)]

    return required, optional


def _score_candidate_for_slot(
    product: Product,
    my_hex_colors: list[str],
    user_tone_id: str,
) -> float:
    """슬롯 후보 아이템의 적합도를 산출한다 (톤 기여도 순 탐욕적 선택)."""
    tone_score = 0.0
    if product.tone_id:
        if product.tone_id == user_tone_id:
            tone_score = 1.0
        elif product.tone_id in COMPATIBLE_TONES.get(user_tone_id, set()):
            tone_score = 0.8
        else:
            tone_score = 0.3

    color_score = 0.5
    if product.color_hex and my_hex_colors:
        p_rgb = _hex_to_rgb(product.color_hex)
        distances = [_rgb_distance(p_rgb, _hex_to_rgb(h)) for h in my_hex_colors]
        min_dist = min(distances)
        color_score = max(0.0, 1.0 - min_dist / 441.67)

    price_score = 0.5
    if product.price and product.price > 0:
        price_score = min(1.0, 80000 / product.price) * 0.5 + 0.5

    return tone_score * 0.45 + color_score * 0.35 + price_score * 0.20


async def _fetch_slot_candidates(
    db: AsyncSession,
    slot_group: str,
    user_tone_id: str,
    gender: str | None,
    age_group: str | None,
    budget_max: int | None,
) -> list[Product]:
    """슬롯에 해당하는 카테고리의 상품 후보를 DB에서 조회한다."""
    from app.services.feed_service import _GROUP_MAP

    target_categories = [cat for cat, grp in _GROUP_MAP.items() if grp == slot_group]
    if not target_categories:
        return []

    stmt = (
        select(Product)
        .where(
            Product.category.in_(target_categories),
            Product.color_hex.isnot(None),
            Product.price.isnot(None),
            Product.price > 0,
            Product.image_url.isnot(None),
        )
    )
    if gender:
        stmt = stmt.where(
            (Product.gender == gender) | (Product.gender == "unisex") | (Product.gender.is_(None))
        )
    if age_group:
        stmt = stmt.where(
            (Product.age_group == age_group) | (Product.age_group.is_(None))
        )
    if budget_max and budget_max > 0:
        stmt = stmt.where(Product.price <= budget_max)

    allowed_tones = {user_tone_id} | COMPATIBLE_TONES.get(user_tone_id, set())
    stmt = stmt.where(
        (Product.tone_id.in_(allowed_tones)) | (Product.tone_id.is_(None))
    )
    stmt = stmt.limit(200)

    result = await db.execute(stmt)
    return list(result.scalars().all())


def _greedy_select_combo(
    slot_candidates: dict[str, list[tuple[Product, float]]],
    required_slots: list[str],
    optional_slots: list[str],
    my_items: list[dict],
    user_tone_id: str,
    budget_max: int | None,
) -> list[dict] | None:
    """탐욕적으로 최적 조합 하나를 선택한다.

    필수 슬롯을 모두 채우지 못하면 None을 반환한다.
    """
    selected: list[Product] = []
    selected_hex: list[str] = [h for it in my_items if (h := it.get("dominant_color_hex"))]
    total_cost = 0

    for slot in required_slots:
        candidates = slot_candidates.get(slot, [])
        if not candidates:
            return None

        best: Product | None = None
        best_score = -1.0
        for product, base_score in candidates:
            if product.id in {s.id for s in selected}:
                continue
            if budget_max and total_cost + (product.price or 0) > budget_max:
                continue
            ch_colors = selected_hex + ([product.color_hex] if product.color_hex else [])
            ch_bonus = 0.0
            if len(ch_colors) >= 2:
                ch_bonus = calculate_ch(ch_colors) / 100.0 * 0.2
            adjusted = base_score + ch_bonus
            if adjusted > best_score:
                best_score = adjusted
                best = product
        if best is None:
            return None
        selected.append(best)
        if best.color_hex:
            selected_hex.append(best.color_hex)
        total_cost += best.price or 0

    for slot in optional_slots:
        candidates = slot_candidates.get(slot, [])
        for product, base_score in candidates:
            if product.id in {s.id for s in selected}:
                continue
            if budget_max and total_cost + (product.price or 0) > budget_max:
                continue
            selected.append(product)
            if product.color_hex:
                selected_hex.append(product.color_hex)
            total_cost += product.price or 0
            break

    return [
        {
            "id": p.id,
            "category": p.category,
            "group": category_to_group(p.category),
            "color_hex": p.color_hex,
            "tone_id": p.tone_id,
            "price": p.price,
            "image_url": p.image_url,
            "brand": p.brand,
        }
        for p in selected
    ]


def _compute_dynamic_scores(
    my_items: list[dict],
    combo_items: list[dict],
    user_tone_id: str,
    budget_max: int | None,
) -> dict[str, float]:
    """동적 조합의 5축 스코어를 실시간 계산한다."""
    all_items = my_items + combo_items

    all_tone_ids = [t for it in all_items if (t := it.get("matched_tone_id") or it.get("tone_id"))]
    all_hex = [h for it in all_items if (h := it.get("dominant_color_hex") or it.get("color_hex"))]
    pcf = calculate_pcf(all_tone_ids, all_hex, user_tone_id) if all_tone_ids else 0.0

    of_score = 50.0

    ch_hex = [h for h in all_hex if h]
    ch = calculate_ch(ch_hex) if len(ch_hex) >= 2 else 50.0

    purchase_cost = sum(it.get("price") or 0 for it in combo_items)
    if purchase_cost == 0:
        pe = 100.0
    elif budget_max and budget_max > 0:
        pe = calculate_pe(purchase_cost, 1, budget_max)
    else:
        pe = 50.0

    sf = 60.0

    return {"pcf": pcf, "of": of_score, "ch": ch, "pe": pe, "sf": sf}


def _build_dynamic_result(
    my_items: list[dict],
    combo_items: list[dict],
    scores: dict[str, float],
    total_score: float,
    user_tone_id: str,
) -> dict:
    """동적 조합 결과를 API 응답 형식으로 조립한다."""
    purchase_total = sum(it.get("price") or 0 for it in combo_items)

    reasons = generate_reasons(
        scores=scores,
        user_tone_id=user_tone_id,
        outfit_tpo=None,
        outfit_id=None,
    )

    result_items = []
    for it in my_items:
        result_items.append({
            "id": str(it["id"]),
            "source": "closet",
            "category": it.get("category"),
            "image_url": it.get("image_url"),
            "label": "내 옷",
        })
    for it in combo_items:
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
        "source": "dynamic_combo",
        "db_outfit_id": None,
        "total_score": total_score,
        "scores": scores,
        "reasons": reasons,
        "items": result_items,
        "purchase_summary": {
            "my_items_count": len(my_items),
            "purchase_items_count": len(combo_items),
            "purchase_total": purchase_total,
        },
    }


async def _generate_dynamic_combos(
    db: AsyncSession,
    *,
    my_items: list[dict],
    user_tone_id: str,
    gender: str | None = None,
    age_group: str | None = None,
    budget_max: int | None = None,
    limit: int = DYNAMIC_COMBO_LIMIT,
) -> list[dict]:
    """전략 B: 동적 코디 조합을 생성한다.

    내 아이템들의 카테고리 그룹에서 빈 슬롯을 파악하고,
    각 슬롯별 최적 아이템을 탐욕적으로 선택하여 조합을 만든다.
    """
    my_groups = []
    for it in my_items:
        raw_cat = it.get("category") or ""
        grp = category_to_group(raw_cat) or raw_cat
        if grp:
            my_groups.append(grp)

    if not my_groups:
        return []

    my_hex_colors = [h for it in my_items if (h := it.get("dominant_color_hex"))]

    required_slots, optional_slots = _determine_needed_slots(my_groups)
    if not required_slots:
        return []

    all_slots = required_slots + optional_slots
    slot_candidates: dict[str, list[tuple[Product, float]]] = {}

    for slot in all_slots:
        products = await _fetch_slot_candidates(
            db, slot, user_tone_id, gender, age_group, budget_max,
        )
        scored = [
            (p, _score_candidate_for_slot(p, my_hex_colors, user_tone_id))
            for p in products
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        slot_candidates[slot] = scored[:SLOT_CANDIDATE_LIMIT]

    results: list[dict] = []

    top_per_slot: dict[str, list[tuple[Product, float]]] = {
        s: cands[:SLOT_CANDIDATE_LIMIT] for s, cands in slot_candidates.items()
    }

    req_options = [
        top_per_slot.get(s, []) for s in required_slots
    ]
    if not all(req_options):
        return []

    req_product_lists = [
        [(p, sc) for p, sc in options[:4]] for options in req_options
    ]

    for combo_tuple in itertools.product(*req_product_lists):
        seen_ids = {p.id for p, _ in combo_tuple}
        if len(seen_ids) < len(combo_tuple):
            continue

        combo_items_raw = []
        total_cost = 0
        for product, _ in combo_tuple:
            combo_items_raw.append({
                "id": product.id,
                "category": product.category,
                "group": category_to_group(product.category),
                "color_hex": product.color_hex,
                "tone_id": product.tone_id,
                "price": product.price,
                "image_url": product.image_url,
                "brand": product.brand,
            })
            total_cost += product.price or 0

        if budget_max and total_cost > budget_max:
            continue

        for slot in optional_slots:
            for product, _ in top_per_slot.get(slot, []):
                if product.id not in seen_ids:
                    if budget_max and total_cost + (product.price or 0) > budget_max:
                        continue
                    combo_items_raw.append({
                        "id": product.id,
                        "category": product.category,
                        "group": category_to_group(product.category),
                        "color_hex": product.color_hex,
                        "tone_id": product.tone_id,
                        "price": product.price,
                        "image_url": product.image_url,
                        "brand": product.brand,
                    })
                    seen_ids.add(product.id)
                    total_cost += product.price or 0
                    break

        scores = _compute_dynamic_scores(my_items, combo_items_raw, user_tone_id, budget_max)
        total_score = calculate_soft_score(scores)

        results.append({
            "combo_items": combo_items_raw,
            "scores": scores,
            "total_score": total_score,
        })

    results.sort(key=lambda r: r["total_score"], reverse=True)
    top = results[:limit]

    return [
        _build_dynamic_result(
            my_items,
            r["combo_items"],
            r["scores"],
            r["total_score"],
            user_tone_id,
        )
        for r in top
    ]


async def _load_closet_items(
    db: AsyncSession,
    closet_item_ids: list[str],
    user_id: str,
) -> list[dict]:
    """closet_items 테이블에서 아이템 정보를 로드한다."""
    from app.models.closet_item import ClosetItem

    if not closet_item_ids:
        return []

    try:
        uuid_ids = [uuid.UUID(cid) for cid in closet_item_ids]
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return []

    result = await db.execute(
        select(ClosetItem).where(
            ClosetItem.id.in_(uuid_ids),
            ClosetItem.user_id == user_uuid,
        )
    )
    rows = result.scalars().all()

    return [
        {
            "id": row.id,
            "category": row.category,
            "dominant_color_hex": row.dominant_color_hex,
            "matched_tone_id": row.matched_tone_id,
            "image_url": row.image_url,
        }
        for row in rows
    ]


async def match_outfits_for_closet_item(
    db: AsyncSession,
    *,
    closet_item_id: str | None = None,
    closet_item_ids: list[str] | None = None,
    user_id: str,
    user_tone_id: str,
    gender: str | None = None,
    age_group: str | None = None,
    tpo: str | None = None,
    budget_max: int | None = None,
    limit: int = 10,
) -> dict:
    """DB 코디에서 내 아이템과 매칭되는 코디를 탐색한다.

    단일 아이템: closet_item_id 사용 (전략 A 우선 → B fallback)
    복수 아이템: closet_item_ids 사용 (전략 B 직행)

    Returns:
        {outfits: [...], total_count: int, strategy_used: str}
    """
    ids_to_load = closet_item_ids or ([closet_item_id] if closet_item_id else [])
    if not ids_to_load:
        return {"outfits": [], "total_count": 0, "strategy_used": "none"}

    my_items = await _load_closet_items(db, ids_to_load, user_id)
    if not my_items:
        return {"outfits": [], "total_count": 0, "strategy_used": "db_match"}

    is_multi = len(my_items) > 1

    # 복수 아이템이면 전략 B 직행
    if is_multi:
        dynamic_results = await _generate_dynamic_combos(
            db,
            my_items=my_items,
            user_tone_id=user_tone_id,
            gender=gender,
            age_group=age_group,
            budget_max=budget_max,
            limit=limit,
        )
        return {
            "outfits": dynamic_results,
            "total_count": len(dynamic_results),
            "strategy_used": "dynamic_combo",
        }

    # 단일 아이템: 전략 A (DB 매칭) 우선
    my_item = my_items[0]
    raw_category = my_item.get("category") or ""
    my_group = category_to_group(raw_category) or raw_category

    if not my_group:
        return {"outfits": [], "total_count": 0, "strategy_used": "db_match"}

    # 색상 정보 없으면 전략 A 건너뛰고 전략 B 직행
    if not my_item.get("dominant_color_hex"):
        dynamic_results = await _generate_dynamic_combos(
            db,
            my_items=[my_item],
            user_tone_id=user_tone_id,
            gender=gender,
            age_group=age_group,
            budget_max=budget_max,
            limit=limit,
        )
        return {
            "outfits": dynamic_results,
            "total_count": len(dynamic_results),
            "strategy_used": "dynamic_combo",
        }

    outfits, item_map = await _load_feed_cache(db)

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

    # 전략 B Fallback: DB 매칭 결과 < 3개이면 동적 조합으로 보충
    if len(results) < 3:
        dynamic_results = await _generate_dynamic_combos(
            db,
            my_items=[my_item],
            user_tone_id=user_tone_id,
            gender=gender,
            age_group=age_group,
            budget_max=budget_max,
            limit=limit - len(results),
        )
        results.extend(dynamic_results)
        strategy = "db_match+dynamic_combo" if candidates else "dynamic_combo"
    else:
        strategy = "db_match"

    return {
        "outfits": results,
        "total_count": len(results),
        "strategy_used": strategy,
    }
