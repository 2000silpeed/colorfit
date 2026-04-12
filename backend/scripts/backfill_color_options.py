"""멀티컬러 상품의 색상 옵션을 Gemini Vision으로 추출해 DB에 저장한다.

대상: color_name = '멀티컬러'이고 color_options가 NULL인 상품.
결과: products.color_options JSONB 컬럼에 [{"name": "블랙", "hex": "#000000"}, ...] 저장.

Usage:
    python scripts/backfill_color_options.py              # 전체 실행
    python scripts/backfill_color_options.py --limit 10   # 테스트 10건
    python scripts/backfill_color_options.py --dry-run    # 대상만 확인
"""

import argparse
import asyncio
import json
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
DB_URL = os.getenv("DATABASE_URL", "")

MODEL = "gemini-2.5-flash"
CONCURRENCY = 3
BATCH_SIZE = 20

PROMPT = (
    "이 패션 상품 이미지를 보고, 이 상품에서 선택 가능한 색상 옵션을 분석해줘.\n\n"
    "규칙:\n"
    "1. 이미지에 여러 색상의 동일 상품이 보이면, 각 색상을 리스트로 나열\n"
    "2. 단일 상품이지만 여러 색이 섞인 패턴이면, 주요 색상 2~3개를 나열\n"
    "3. 각 색상에 대해 한글 이름과 HEX 코드를 제공\n"
    "4. 최대 5개까지만\n\n"
    "JSON 배열로만 답해. 설명 없이.\n"
    '예: [{"name": "블랙", "hex": "#000000"}, {"name": "화이트", "hex": "#FFFFFF"}]'
)


async def fetch_image(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.warning("이미지 다운 실패 %s: %s", url[:60], e)
        return None


async def extract_colors(client: genai.Client, img_bytes: bytes) -> list[dict] | None:
    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                PROMPT,
            ],
        )
        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            raw = raw.rsplit("```", 1)[0]
        colors = json.loads(raw)
        return [{"name": c["name"], "hex": c["hex"]} for c in colors[:5]]
    except Exception as e:
        logger.warning("색상 추출 실패: %s", e)
        return None


async def process_one(
    sem: asyncio.Semaphore,
    gemini: genai.Client,
    engine,
    product_id: str,
    image_url: str,
    dry_run: bool,
) -> bool:
    async with sem:
        if dry_run:
            logger.info("[DRY] %s", product_id)
            return True

        img = await fetch_image(image_url)
        if not img:
            return False

        colors = await extract_colors(gemini, img)
        if not colors:
            return False

        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE products SET color_options = :opts WHERE id = :pid"),
                {"opts": json.dumps(colors, ensure_ascii=False), "pid": product_id},
            )

        logger.info("✓ %s → %d colors", product_id, len(colors))
        return True


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    engine = create_async_engine(DB_URL)
    gemini = genai.Client(api_key=API_KEY)
    sem = asyncio.Semaphore(CONCURRENCY)

    async with engine.begin() as conn:
        query = "SELECT id, image_url FROM products WHERE color_name = '멀티컬러' AND color_options IS NULL AND image_url IS NOT NULL"
        if args.limit:
            query += f" LIMIT {args.limit}"
        rows = (await conn.execute(text(query))).fetchall()

    logger.info("대상: %d건", len(rows))

    if not rows:
        return

    t0 = time.time()
    ok = 0
    fail = 0

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        results = await asyncio.gather(*[
            process_one(sem, gemini, engine, r[0], r[1], args.dry_run)
            for r in batch
        ])
        ok += sum(1 for r in results if r)
        fail += sum(1 for r in results if not r)
        logger.info("진행: %d/%d (성공 %d, 실패 %d)", i + len(batch), len(rows), ok, fail)

    elapsed = time.time() - t0
    logger.info("완료: %.1f초, 성공 %d, 실패 %d", elapsed, ok, fail)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
