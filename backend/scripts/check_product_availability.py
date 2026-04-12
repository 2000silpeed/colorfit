"""상품 판매 상태 검증 스크립트.

네이버 쇼핑 API로 상품 존재 여부를 확인하고,
검색 결과에 없는 상품을 is_active = false로 갱신한다.

Usage:
    python scripts/check_product_availability.py              # 전체 실행
    python scripts/check_product_availability.py --limit 100  # 테스트 100건
    python scripts/check_product_availability.py --dry-run    # 변경 없이 확인만
    python scripts/check_product_availability.py --stale-days 30  # 30일 이상 미확인 상품만
"""

import argparse
import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

CONCURRENCY = 1
BATCH_SIZE = 10
API_DELAY = 0.15  # 네이버 API rate limit 대응 (초당 ~6건)


async def check_product(
    http: httpx.AsyncClient,
    product_id: str,
    product_name: str,
) -> bool:
    """네이버 쇼핑 API로 상품 존재 여부를 확인한다."""
    try:
        resp = await http.get(
            "https://openapi.naver.com/v1/search/shop.json",
            params={"query": product_name[:50], "display": 5},
            headers={
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return False
        for item in items:
            if item.get("productId") == product_id:
                return True
        return len(items) > 0
    except Exception as e:
        logger.warning("API 호출 실패 %s: %s", product_id, e)
        return True  # 에러 시 안전하게 활성 유지


async def process_batch(
    sem: asyncio.Semaphore,
    http: httpx.AsyncClient,
    engine,
    products: list[tuple],
    dry_run: bool,
) -> tuple[int, int]:
    """배치 단위로 검증 후 DB 업데이트."""
    deactivated = 0
    reactivated = 0

    async def check_one(pid: str, name: str, currently_active: bool):
        nonlocal deactivated, reactivated
        async with sem:
            is_available = await check_product(http, pid, name or "")
            await asyncio.sleep(API_DELAY)

            if currently_active and not is_available:
                if not dry_run:
                    async with engine.begin() as conn:
                        await conn.execute(
                            text("UPDATE products SET is_active = false WHERE id = :pid"),
                            {"pid": pid},
                        )
                logger.info("비활성: %s (%s)", pid, (name or "")[:40])
                deactivated += 1
            elif not currently_active and is_available:
                if not dry_run:
                    async with engine.begin() as conn:
                        await conn.execute(
                            text("UPDATE products SET is_active = true WHERE id = :pid"),
                            {"pid": pid},
                        )
                logger.info("재활성: %s (%s)", pid, (name or "")[:40])
                reactivated += 1

    await asyncio.gather(*[
        check_one(p[0], p[1], p[2]) for p in products
    ])

    return deactivated, reactivated


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stale-days", type=int, default=0,
                        help="N일 이상 미확인 상품만 (0이면 전체)")
    args = parser.parse_args()

    engine = create_async_engine(DB_URL)
    sem = asyncio.Semaphore(CONCURRENCY)

    query = "SELECT id, name, is_active FROM products WHERE image_url IS NOT NULL"
    if args.stale_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.stale_days)
        query += f" AND (last_observed_at IS NULL OR last_observed_at < '{cutoff.isoformat()}')"
    if args.limit:
        query += f" LIMIT {args.limit}"

    async with engine.begin() as conn:
        rows = (await conn.execute(text(query))).fetchall()

    logger.info("검증 대상: %d건 (dry_run=%s)", len(rows), args.dry_run)

    if not rows:
        await engine.dispose()
        return

    t0 = time.time()
    total_deactivated = 0
    total_reactivated = 0

    async with httpx.AsyncClient(timeout=10.0) as http:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            d, r = await process_batch(sem, http, engine, batch, args.dry_run)
            total_deactivated += d
            total_reactivated += r

            if (i + BATCH_SIZE) % 100 == 0 or i + BATCH_SIZE >= len(rows):
                logger.info(
                    "진행: %d/%d (비활성 %d, 재활성 %d)",
                    min(i + BATCH_SIZE, len(rows)), len(rows),
                    total_deactivated, total_reactivated,
                )

    # last_observed_at 갱신
    if not args.dry_run:
        checked_ids = [r[0] for r in rows]
        for i in range(0, len(checked_ids), 500):
            batch_ids = checked_ids[i:i + 500]
            placeholders = ",".join(f"'{pid}'" for pid in batch_ids)
            async with engine.begin() as conn:
                await conn.execute(text(
                    f"UPDATE products SET last_observed_at = NOW() WHERE id IN ({placeholders})"
                ))

    elapsed = time.time() - t0
    logger.info(
        "완료: %.1f초, 비활성 %d건, 재활성 %d건",
        elapsed, total_deactivated, total_reactivated,
    )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
