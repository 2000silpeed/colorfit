"""아이템 상세 + 유사 상품 API.

기획서 섹션 8.4.4, 14.3 구현.
GET /api/item/{id} — 아이템 상세 + 판매처별 가격
GET /api/item/{id}/similar — 유사 상품 리스트
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.product import Product
from app.schemas.item import (
    ItemDetailResponse,
    PriceEntry,
    SimilarListResponse,
    SimilarProductResponse,
)
from app.services.similar_finder import find_similar_products

router = APIRouter(prefix="/api", tags=["item"])


async def _find_price_entries(
    db: AsyncSession,
    source: Product,
) -> list[PriceEntry]:
    """동일 상품의 판매처별 가격을 조회한다.

    동일 이름+브랜드인 상품들을 찾아 판매처별로 그룹화.
    """
    if not source.name or not source.brand:
        entries = []
        if source.mall_name and source.price and source.mall_url:
            entries.append(
                PriceEntry(
                    mall_name=source.mall_name,
                    price=source.price,
                    mall_url=source.mall_url,
                    is_lowest=True,
                )
            )
        return entries

    stmt = select(Product).where(
        Product.name == source.name,
        Product.brand == source.brand,
        Product.price.isnot(None),
        Product.price > 0,
        Product.mall_url.isnot(None),
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    best_by_mall: dict[str, PriceEntry] = {}
    for row in rows:
        key = row.mall_name or row.id
        price = row.price  # type: ignore[arg-type]
        if key not in best_by_mall or price < best_by_mall[key].price:
            best_by_mall[key] = PriceEntry(
                mall_name=row.mall_name or "기타",
                price=price,
                mall_url=row.mall_url or "",
            )
    entries = list(best_by_mall.values())

    entries.sort(key=lambda e: e.price)
    if entries:
        entries[0].is_lowest = True

    return entries


@router.get("/item/{item_id}", response_model=ItemDetailResponse)
async def get_item_detail(
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> ItemDetailResponse:
    product = await db.get(Product, item_id)
    if product is None:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    price_entries = await _find_price_entries(db, product)

    return ItemDetailResponse(
        id=product.id,
        name=product.name,
        brand=product.brand,
        category=product.category,
        color_hex=product.color_hex,
        tone_id=product.tone_id,
        price=product.price,
        mall_name=product.mall_name,
        mall_url=product.mall_url,
        image_url=product.image_url,
        gender=product.gender,
        silhouette=product.silhouette,
        formality=product.formality,
        price_entries=price_entries,
    )


@router.get("/item/{item_id}/check-availability")
async def check_availability(
    item_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """상품 판매 링크 유효성을 실시간 체크한다."""
    product = await db.get(Product, item_id)
    if product is None:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    if not product.mall_url:
        return {"available": False, "reason": "판매 링크 없음"}

    try:
        async with httpx.AsyncClient(
            timeout=5.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            resp = await client.head(product.mall_url)
            available = resp.status_code < 400
    except httpx.HTTPError:
        available = True

    if not available and product.is_active:
        product.is_active = False
        await db.commit()

    return {
        "available": available,
        "mall_url": product.mall_url,
        "reason": None if available else "판매 종료된 상품이에요",
    }


@router.get("/item/{item_id}/similar", response_model=SimilarListResponse)
async def get_similar_items(
    item_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> SimilarListResponse:
    product = await db.get(Product, item_id)
    if product is None:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    results = await find_similar_products(db, item_id, limit=limit)

    similar = [
        SimilarProductResponse(
            id=r["product"].id,
            name=r["product"].name,
            brand=r["product"].brand,
            price=r["product"].price,
            image_url=r["product"].image_url,
            mall_url=r["product"].mall_url,
            similarity=round(r["similarity"] * 100, 1),
            match_type=r["match_type"],
        )
        for r in results
    ]

    return SimilarListResponse(source_id=item_id, similar=similar)
