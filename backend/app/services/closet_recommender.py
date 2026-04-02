"""보유 옷 기반 역방향 추천 서비스.

사용자 옷의 색상/카테고리를 기반으로
어울리는 상품을 TPO별로 추천한다.
기획서 F-39 구현.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.services.similar_finder import _color_similarity, _hex_to_rgb
from app.services.scoring import COMPATIBLE_TONES

TPO_LABELS: dict[str, str] = {
    "commute": "출근 코디",
    "date": "데이트 코디",
    "weekend": "주말 코디",
    "campus": "캠퍼스 코디",
    "interview": "면접 코디",
    "travel": "여행 코디",
    "event": "행사 코디",
    "workout": "운동 코디",
}

COMPLEMENTARY_CATEGORIES: dict[str, list[str]] = {
    "상의": ["하의", "아우터", "신발", "가방"],
    "하의": ["상의", "아우터", "신발", "가방"],
    "아우터": ["상의", "하의", "신발"],
    "원피스": ["아우터", "신발", "가방"],
    "신발": ["상의", "하의", "가방"],
    "가방": ["상의", "하의", "원피스"],
}

TPO_FORMALITY: dict[str, tuple[int, int]] = {
    "commute": (3, 5),
    "date": (2, 4),
    "weekend": (1, 3),
    "campus": (1, 3),
    "interview": (4, 5),
    "travel": (1, 3),
    "event": (3, 5),
    "workout": (1, 2),
}


def _tone_compatible(item_tone_id: str | None, user_tone_id: str) -> bool:
    """아이템 톤이 사용자 톤과 호환되는지 확인."""
    if not item_tone_id:
        return False
    if item_tone_id == user_tone_id:
        return True
    return item_tone_id in COMPATIBLE_TONES.get(user_tone_id, set())


def _color_harmony_score(source_hex: str, candidate_hex: str) -> float:
    """소스 색상과 후보 색상의 조화도 (0.0~1.0).

    색상 유사도 기반 — 보색/유사색 모두 높은 점수.
    """
    similarity = _color_similarity(source_hex, candidate_hex)
    complementary = 1.0 - similarity
    return max(similarity, complementary * 0.8)


def _compute_recommendation_score(
    source_hex: str,
    candidate: Product,
    user_tone_id: str,
) -> float:
    """추천 점수 산출.

    톤 호환 40% + 색상 조화 40% + 가격 보너스 20%
    """
    tone_score = 1.0 if _tone_compatible(candidate.tone_id, user_tone_id) else 0.3

    color_score = 0.5
    if candidate.color_hex and source_hex:
        color_score = _color_harmony_score(source_hex, candidate.color_hex)

    price_score = 0.5
    if candidate.price and candidate.price > 0:
        price_score = min(1.0, 50000 / candidate.price) * 0.5 + 0.5

    return round(tone_score * 0.4 + color_score * 0.4 + price_score * 0.2, 4)


def _match_reason(
    candidate: Product,
    user_tone_id: str,
    source_hex: str,
) -> str:
    """추천 이유를 한 줄로 생성."""
    if _tone_compatible(candidate.tone_id, user_tone_id):
        return "퍼스널컬러에 잘 맞는 아이템이에요"
    if candidate.color_hex and source_hex:
        harmony = _color_harmony_score(source_hex, candidate.color_hex)
        if harmony >= 0.7:
            return "보유 옷과 색상 조화가 좋아요"
    return "카테고리가 잘 어울리는 아이템이에요"


async def recommend_for_closet_item(
    db: AsyncSession,
    source_color_hex: str,
    source_category: str,
    user_tone_id: str,
    tpo_list: list[str] | None = None,
    limit_per_tpo: int = 4,
) -> list[dict]:
    """보유 옷 기반으로 TPO별 추천 상품을 반환한다.

    Args:
        db: DB 세션
        source_color_hex: 보유 옷의 대표 색상
        source_category: 보유 옷의 카테고리
        user_tone_id: 사용자 퍼스널컬러 톤 ID
        tpo_list: 필터링할 TPO 목록 (None이면 전체)
        limit_per_tpo: TPO당 추천 개수

    Returns:
        TPO별 추천 리스트
    """
    target_categories = COMPLEMENTARY_CATEGORIES.get(source_category, ["상의", "하의"])

    stmt = (
        select(Product)
        .where(
            Product.category.in_(target_categories),
            Product.color_hex.isnot(None),
            Product.price.isnot(None),
            Product.price > 0,
            Product.image_url.isnot(None),
        )
        .limit(500)
    )
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    active_tpos = tpo_list or list(TPO_LABELS.keys())

    tpo_results: list[dict] = []
    for tpo in active_tpos:
        if tpo not in TPO_LABELS:
            continue

        formality_range = TPO_FORMALITY.get(tpo, (1, 5))

        tpo_candidates: list[tuple[Product, float]] = []
        for c in candidates:
            if c.formality is not None:
                if not (formality_range[0] <= c.formality <= formality_range[1]):
                    continue

            score = _compute_recommendation_score(
                source_hex=source_color_hex,
                candidate=c,
                user_tone_id=user_tone_id,
            )
            tpo_candidates.append((c, score))

        tpo_candidates.sort(key=lambda x: x[1], reverse=True)
        top = tpo_candidates[:limit_per_tpo]

        items = []
        for product, score in top:
            items.append({
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "category": product.category,
                "price": product.price,
                "image_url": product.image_url,
                "mall_url": product.mall_url,
                "color_hex": product.color_hex,
                "similarity": round(score * 100, 1),
                "match_reason": _match_reason(product, user_tone_id, source_color_hex),
            })

        if items:
            tpo_results.append({
                "tpo": tpo,
                "tpo_label": TPO_LABELS[tpo],
                "items": items,
            })

    return tpo_results
