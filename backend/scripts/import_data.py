"""normalized/*.json + generated_outfits.json → Supabase DB Import."""

import asyncio
import json
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from app.config import settings

BATCH_SIZE = 500


async def import_products(conn: asyncpg.Connection):
    """normalized/*.json → products 테이블."""
    files = sorted(glob.glob("data/normalized/*.json"))
    total = 0

    for filepath in files:
        with open(filepath) as f:
            data = json.load(f)

        items = data["items"]
        tone = data["tone_id"]
        rows = []
        for item in items:
            rows.append((
                item["product_id"],
                item.get("name"),
                item.get("brand"),
                item.get("category"),
                item.get("color_hex"),
                item.get("tone_id", tone),
                item.get("price"),
                item.get("mall_name"),
                item.get("mall_url"),
                item.get("image_url"),
                item.get("tags") or None,
                item.get("gender"),
                item.get("silhouette"),
                item.get("formality"),
            ))

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            await conn.executemany(
                """INSERT INTO products (id, name, brand, category, color_hex, tone_id,
                   price, mall_name, mall_url, image_url, tags, gender, silhouette, formality)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                   ON CONFLICT (id) DO NOTHING""",
                batch,
            )

        total += len(rows)
        print(f"  {tone}: {len(rows)}건")

    print(f"  → products 총 {total}건 import")
    return total


async def import_outfits(conn: asyncpg.Connection):
    """generated_outfits.json → outfits 테이블."""
    with open("data/generated_outfits.json") as f:
        data = json.load(f)

    outfits = data["outfits"]
    rows = []
    seen_ids = set()
    for o in outfits:
        tags = o.get("tags", [])
        tone = tags[0] if tags else "unknown"
        unique_id = f"{o['id']}_{tone}"
        if unique_id in seen_ids:
            continue
        seen_ids.add(unique_id)
        rows.append((
            unique_id,
            o.get("item_ids"),
            o.get("gender"),
            o.get("age_group"),
            o.get("designed_tpo"),
            o.get("designed_season"),
            o.get("designed_moods"),
            o.get("total_price"),
            o.get("lowest_total_price"),
            o.get("is_complete_outfit"),
            o.get("tags"),
            json.dumps(o["scores"]) if o.get("scores") else None,
            json.dumps(o["style_details"]) if o.get("style_details") else None,
            o.get("reasons"),
            o.get("llm_quality_score"),
        ))

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        await conn.executemany(
            """INSERT INTO outfits (id, item_ids, gender, age_group, designed_tpo, designed_season,
               designed_moods, total_price, lowest_total_price, is_complete_outfit,
               tags, scores, style_details, reasons, llm_quality_score)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12::jsonb,$13::jsonb,$14,$15)
               ON CONFLICT (id) DO NOTHING""",
            batch,
        )

    print(f"  → outfits 총 {len(outfits)}건 import")
    return len(outfits)


async def main():
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    print(f"DB: {url[:60]}...")

    conn = await asyncpg.connect(url, statement_cache_size=0)
    try:
        print("\n[1/2] Products import...")
        prod_count = await import_products(conn)

        print("\n[2/2] Outfits import...")
        outfit_count = await import_outfits(conn)

        # 검증
        p = await conn.fetchval("SELECT count(*) FROM products")
        o = await conn.fetchval("SELECT count(*) FROM outfits")
        print(f"\n✅ Import 완료 — DB 내 products: {p}, outfits: {o}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
