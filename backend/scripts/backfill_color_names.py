"""Gemini Vision으로 코디용 상품 이미지에서 한글 색상명을 추출한다.

대상: outfits.item_ids에 포함된 상품 중 color_name이 NULL인 것.
결과: products.color_name 컬럼에 저장.

Usage:
    python scripts/backfill_color_names.py              # 전체 실행
    python scripts/backfill_color_names.py --limit 10   # 테스트 10건
    python scripts/backfill_color_names.py --dry-run    # API 호출 없이 대상만 확인
"""

import argparse
import asyncio
import logging
import os
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = (
    os.getenv("DATABASE_URL", "")
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("postgres://", "postgresql+asyncpg://")
)

MODEL = "gemini-2.5-flash"
CONCURRENCY = 5
BATCH_SIZE = 50

VALID_COLORS = frozenset({
    "블랙", "차콜", "그레이", "라이트그레이", "화이트", "아이보리", "크림", "베이지", "샌드",
    "카멜", "브라운", "다크브라운", "탄", "테라코타", "버건디", "와인", "레드", "코랄",
    "로즈", "핑크", "라이트핑크", "오렌지", "머스타드", "옐로", "골드", "올리브", "카키",
    "그린", "다크그린", "민트", "틸", "스카이블루", "라이트블루", "블루", "네이비", "인디고",
    "라벤더", "라일락", "퍼플", "바이올렛", "실버", "멀티컬러", "데님", "누드",
})

PROMPT = (
    "이 패션 상품 이미지의 주요 색상을 한글로 답해.\n"
    "규칙:\n"
    "- 반드시 아래 목록 중 하나만 답할 것\n"
    "- 배경색이 아니라 상품 자체의 색상을 답할 것\n"
    "- 답변은 색상명 한 단어만 (설명 없이)\n\n"
    "[색상 목록]\n"
    + ", ".join(sorted(VALID_COLORS))
)


async def fetch_image(client: httpx.AsyncClient, url: str) -> bytes | None:
    try:
        resp = await client.get(url, timeout=10, follow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return resp.content
    except Exception:
        pass
    return None


def extract_color_sync(gemini: genai.Client, image_bytes: bytes) -> str | None:
    try:
        response = gemini.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                PROMPT,
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=20,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        if response.text:
            color = response.text.strip().replace(" ", "")
            logger.debug("Gemini raw: '%s'", color)
            if color not in VALID_COLORS:
                logger.info("Gemini 응답 '%s' → VALID_COLORS에 없음", color)
            return color if color in VALID_COLORS else None
    except Exception as e:
        logger.warning("Gemini error: %s", e)
    return None


async def process_batch(
    engine,
    gemini: genai.Client,
    http: httpx.AsyncClient,
    rows: list[tuple[str, str]],
    dry_run: bool,
) -> int:
    updated = 0
    sem = asyncio.Semaphore(CONCURRENCY)
    loop = asyncio.get_event_loop()

    async def process_one(product_id: str, image_url: str):
        nonlocal updated
        async with sem:
            img = await fetch_image(http, image_url)
            if not img:
                return

            if dry_run:
                logger.info("[dry-run] %s → would call Gemini", product_id[:20])
                return

            color = await loop.run_in_executor(
                None, extract_color_sync, gemini, img
            )
            if not color:
                return

            async with engine.begin() as conn:
                await conn.execute(
                    text("UPDATE products SET color_name = :color WHERE id = :pid"),
                    {"color": color, "pid": product_id},
                )
            updated += 1

    await asyncio.gather(*[process_one(pid, url) for pid, url in rows])
    return updated


async def main(limit: int | None, dry_run: bool):
    engine = create_async_engine(DATABASE_URL, pool_size=10)
    gemini = genai.Client(api_key=API_KEY)

    async with engine.begin() as conn:
        query = """
            SELECT DISTINCT p.id, p.image_url
            FROM products p
            JOIN (SELECT unnest(item_ids) AS pid FROM outfits) oi ON oi.pid = p.id
            WHERE p.image_url IS NOT NULL
              AND p.color_name IS NULL
        """
        if limit:
            query += f" LIMIT {limit}"
        result = await conn.execute(text(query))
        rows = [(r[0], r[1]) for r in result]

    total = len(rows)
    logger.info("처리 대상: %d건 (dry_run=%s)", total, dry_run)

    if total == 0:
        logger.info("처리할 항목 없음")
        await engine.dispose()
        return

    total_updated = 0
    start = time.time()

    async with httpx.AsyncClient() as http:
        for i in range(0, total, BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            updated = await process_batch(engine, gemini, http, batch, dry_run)
            total_updated += updated
            processed = i + len(batch)
            elapsed = time.time() - start
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed) / rate / 60 if rate > 0 else 0
            logger.info(
                "진행: %d/%d (%.0f건/분) | 업데이트: %d건 | ETA: %.1f분",
                processed, total, rate * 60, total_updated, eta,
            )

    elapsed = time.time() - start
    logger.info("완료: %d건 중 %d건 업데이트, %.1f분 소요", total, total_updated, elapsed / 60)
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Vision 기반 상품 색상명 추출")
    parser.add_argument("--limit", type=int, default=None, help="처리 건수 제한 (테스트용)")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 대상만 확인")
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.dry_run))
