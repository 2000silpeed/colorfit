"""normalized/*.json 상품에 category, gender, formality를 채우고 DB를 업데이트한다.

Task 1.8 결과를 normalized JSON에 반영 + Supabase products 테이블 UPDATE.
"""

import asyncio
import json
import glob
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from app.config import settings
from app.services.category_classifier import classify_by_keyword, _CATEGORY_TO_GROUP

# raw_category2 → gender
RAW_GENDER_MAP: dict[str, str] = {
    "여성의류": "female", "여성신발": "female", "여성가방": "female",
    "여성언더웨어/잠옷": "female", "임부복": "female",
    "남성의류": "male", "남성신발": "male", "남성가방": "male",
    "남성언더웨어/잠옷": "male",
}

# category → 기본 formality
DEFAULT_FORMALITY: dict[str, int] = {
    "코트": 4, "자켓": 4, "블레이저": 5, "가디건": 3, "패딩": 2, "점퍼": 2, "조끼": 3,
    "셔츠": 4, "블라우스": 4, "니트": 3, "티셔츠": 2, "맨투맨": 2, "후드": 1,
    "크롭탑": 1, "탱크탑": 1, "폴로": 3,
    "슬랙스": 4, "청바지": 2, "스커트": 3, "와이드팬츠": 3,
    "조거팬츠": 1, "숏팬츠": 1, "레깅스": 1, "치노": 3,
    "원피스": 3,
    "스니커즈": 2, "로퍼": 4, "힐": 4, "부츠": 3, "샌들": 2, "더비": 5,
    "가방": 3, "액세서리": 3,
}

# 패션 관련 raw_category2만 허용
FASHION_CATEGORIES = {
    "여성의류", "남성의류", "여성신발", "남성신발", "여성가방", "남성가방",
    "주얼리", "패션소품", "모자", "벨트", "장갑", "선글라스/안경테",
    "시계", "양말",
}


def classify_item(item: dict) -> dict:
    """상품 1건 분류. category, group, gender, formality 반환."""
    result = classify_by_keyword(
        item.get("name", ""),
        item.get("raw_category3"),
        item.get("raw_category4"),
    )
    category = result["category"] if result else None
    group = result["group"] if result else ""

    raw_cat2 = item.get("raw_category2", "")
    gender = RAW_GENDER_MAP.get(raw_cat2, "unisex")
    formality = DEFAULT_FORMALITY.get(category, 3) if category else None

    return {
        "category": category,
        "group": group,
        "gender": gender,
        "formality": formality,
    }


def process_normalized_files() -> tuple[int, int, int]:
    """normalized JSON 파일들에 분류 결과를 write-back한다."""
    files = sorted(glob.glob("data/normalized/*.json"))
    total = 0
    classified = 0
    non_fashion = 0

    for filepath in files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        tone_id = data["tone_id"]
        updated_items = []

        for item in data["items"]:
            total += 1
            raw_cat2 = item.get("raw_category2", "")

            if raw_cat2 and raw_cat2 not in FASHION_CATEGORIES:
                non_fashion += 1
                continue

            result = classify_item(item)
            item["category"] = result["category"]
            item["gender"] = result["gender"]
            item["formality"] = result["formality"]

            if result["category"]:
                classified += 1

            updated_items.append(item)

        data["items"] = updated_items
        data["item_count"] = len(updated_items)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  {tone_id}: {len(updated_items)}건 (비패션 제거 {len(data.get('items', [])) - len(updated_items) if False else ''})")

    return total, classified, non_fashion


async def update_db():
    """DB products 테이블에 category, gender, formality 업데이트."""
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url, statement_cache_size=0)

    try:
        # 비패션 상품 삭제
        files = sorted(glob.glob("data/normalized/*.json"))
        valid_ids = set()
        updates = []

        for filepath in files:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            for item in data["items"]:
                pid = item["product_id"]
                valid_ids.add(pid)
                if item.get("category"):
                    updates.append((
                        item["category"],
                        item.get("gender"),
                        item.get("formality"),
                        pid,
                    ))

        # 비패션 상품 DB에서 삭제
        db_count = await conn.fetchval("SELECT count(*) FROM products")
        deleted = await conn.execute(
            "DELETE FROM products WHERE id != ALL($1::text[])",
            list(valid_ids),
        )
        print(f"\n  비패션 상품 삭제: {deleted}")

        # category, gender, formality 업데이트
        BATCH = 500
        for i in range(0, len(updates), BATCH):
            batch = updates[i:i + BATCH]
            await conn.executemany(
                "UPDATE products SET category=$1, gender=$2, formality=$3 WHERE id=$4",
                batch,
            )

        # 검증
        cat_count = await conn.fetchval("SELECT count(*) FROM products WHERE category IS NOT NULL")
        total = await conn.fetchval("SELECT count(*) FROM products")
        print(f"  DB 업데이트 완료: {cat_count}/{total} 상품에 category 설정됨")

        # 분포 확인
        rows = await conn.fetch(
            "SELECT category, count(*) as cnt FROM products WHERE category IS NOT NULL GROUP BY category ORDER BY cnt DESC LIMIT 15"
        )
        print("\n  카테고리 분포 (상위 15):")
        for r in rows:
            print(f"    {r['category']}: {r['cnt']}")

    finally:
        await conn.close()


async def main():
    print("[1/2] Normalized JSON 분류 + write-back...")
    total, classified, non_fashion = process_normalized_files()
    print(f"\n  총 {total}건 → 분류됨 {classified}건, 비패션 제거 {non_fashion}건")

    print("\n[2/2] DB 업데이트...")
    await update_db()

    print("\n✅ 상품 분류 완료")


if __name__ == "__main__":
    asyncio.run(main())
