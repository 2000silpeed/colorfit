"""유사 상품 매칭 서비스.

기준 상품에 대해 색상·가격 유사도로 대안 상품을 찾는다.
Exact(동일 상품 다른 판매처) / Similar(대체재)를 구분한다.
기획서 섹션 6.2 구현.
"""

from __future__ import annotations

import math
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

_MAX_RGB_DISTANCE = 441.67  # sqrt(255^2 * 3)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _color_similarity(hex1: str, hex2: str) -> float:
    """두 HEX 색상 간 유사도 (0.0~1.0)."""
    rgb1 = _hex_to_rgb(hex1)
    rgb2 = _hex_to_rgb(hex2)
    dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))
    return 1.0 - dist / _MAX_RGB_DISTANCE


def _price_similarity(price1: int, price2: int) -> float:
    """두 가격 간 유사도 (0.0~1.0)."""
    if price1 <= 0 or price2 <= 0:
        return 0.0
    return min(price1, price2) / max(price1, price2)


def _normalize_name(name: str) -> str:
    """상품명 정규화 — 공백/특수문자 제거, 소문자, NFKC."""
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"[^a-z가-힣0-9]", "", name.lower())
    return name


def classify_match_type(
    source_name: str | None,
    source_brand: str | None,
    candidate_name: str | None,
    candidate_brand: str | None,
) -> str:
    """Exact(동일 상품 다른 판매처) vs Similar(대체재) 판별."""
    if not source_name or not candidate_name:
        return "similar"
    if not source_brand or not candidate_brand:
        return "similar"

    if (
        _normalize_name(source_name) == _normalize_name(candidate_name)
        and source_brand.strip().lower() == candidate_brand.strip().lower()
    ):
        return "exact"
    return "similar"


def compute_similarity(
    source_hex: str,
    source_price: int,
    candidate_hex: str,
    candidate_price: int,
) -> float:
    """총합 유사도 점수 (0.0~1.0).

    color_similarity × 0.6 + price_similarity × 0.4
    """
    cs = _color_similarity(source_hex, candidate_hex)
    ps = _price_similarity(source_price, candidate_price)
    return round(cs * 0.6 + ps * 0.4, 4)


async def find_similar_products(
    db: AsyncSession,
    product_id: str,
    limit: int = 5,
) -> list[dict]:
    """기준 상품과 유사한 상품 상위 N개를 반환한다.

    Args:
        db: DB 세션
        product_id: 기준 상품 ID
        limit: 반환 개수 (기본 5)

    Returns:
        유사도 내림차순 리스트. 각 항목:
        {product, similarity, match_type}
    """
    source = await db.get(Product, product_id)
    if source is None:
        return []

    if not source.category or not source.color_hex or not source.price:
        return []

    stmt = (
        select(Product)
        .where(
            Product.category == source.category,
            Product.id != source.id,
            Product.color_hex.isnot(None),
            Product.price.isnot(None),
            Product.price > 0,
        )
    )
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    scored: list[tuple[Product, float, str]] = []
    for c in candidates:
        similarity = compute_similarity(
            source.color_hex, source.price,
            c.color_hex, c.price,  # type: ignore[arg-type]
        )
        match_type = classify_match_type(
            source.name, source.brand,
            c.name, c.brand,
        )
        scored.append((c, similarity, match_type))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    return [
        {
            "product": p,
            "similarity": s,
            "match_type": mt,
        }
        for p, s, mt in top
    ]
