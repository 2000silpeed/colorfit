"""normalized/*.json 상품에 category, gender, formality, age_group을 채우고 DB를 업데이트한다.

Task 1.8 + 연령대 분류. Supabase products 테이블 반영.
"""

import asyncio
import json
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from app.config import settings
from app.services.category_classifier import classify_by_keyword, _CATEGORY_TO_GROUP

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

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

FASHION_CATEGORIES = {
    "여성의류", "남성의류", "여성신발", "남성신발", "여성가방", "남성가방",
    "주얼리", "패션소품", "모자", "벨트", "장갑", "선글라스/안경테",
    "시계", "양말",
}

# 비일상복 키워드 — 이 키워드가 상품명에 포함되면 제외
EXCLUDE_KEYWORDS = [
    "무용", "연습복", "공연", "무대 의상", "노래교실", "난타복", "트로트",
    "한복", "코스프레", "코스튬", "할로윈", "유니폼", "단체복",
    "잠옷", "파자마", "수영복", "비키니", "래시가드",
    "등산복", "낚시", "작업복", "안전화", "스키복",
    "입시복", "한국무용", "발레복", "체조복",
    "초등", "유아", "아동", "키즈", "아기", "돌잔치",
    "반려동물", "애완", "강아지", "고양이",
    "커플티", "단체티", "사은품", "판촉",
]

# ── 연령대 분류 ──

AGE_KEYWORDS: dict[str, list[str]] = {
    "20s": [
        "y2k", "캠퍼스", "대학생", "스트리트", "크롭", "오버핏", "유니",
        "힙합", "스케이트", "빈티지", "레트로", "뉴진스", "아이돌",
        "하이틴", "교복", "10대", "20대", "영캐주얼",
    ],
    "40plus": [
        "엄마옷", "엄마", "중년", "어머니", "미시", "마담", "시니어",
        "40대", "50대", "60대", "빅사이즈", "여유핏", "편한",
        "아줌마", "할머니", "실버",
    ],
}

# 브랜드 → 연령대 매핑 (소문자 키)
_brand_age_map: dict[str, str] | None = None


def _load_brand_age_map() -> dict[str, str]:
    global _brand_age_map
    if _brand_age_map is None:
        with open(DATA_DIR / "brand_age_map.json", encoding="utf-8") as f:
            raw = json.load(f)
        _brand_age_map = {}
        for age_group, brands in raw.items():
            for brand in brands:
                _brand_age_map[brand.lower()] = age_group
    return _brand_age_map


# 카테고리별 가격 기반 연령대 임계값 (원)
PRICE_AGE_THRESHOLDS: dict[str, tuple[int, int]] = {
    # (20s 상한, 30s 상한) — 초과하면 40plus
    "top": (25000, 60000),
    "outer": (60000, 180000),
    "bottom": (30000, 80000),
    "onepiece": (40000, 100000),
    "shoes": (50000, 120000),
    "bag": (50000, 150000),
    "acc": (30000, 80000),
}

# 카테고리별 연령대 보정
CATEGORY_AGE_BIAS: dict[str, str] = {
    "후드": "20s", "맨투맨": "20s", "크롭탑": "20s", "탱크탑": "20s",
    "조거팬츠": "20s", "숏팬츠": "20s", "스니커즈": "20s",
    "블라우스": "30s", "슬랙스": "30s", "로퍼": "30s", "더비": "30s",
}


def classify_age_group(item: dict, category: str | None, group: str | None) -> str:
    """상품의 연령대를 3단계 휴리스틱으로 분류."""
    name = item.get("name", "").lower()
    brand = item.get("brand", "")
    price = item.get("price") or 0

    # 1단계: 키워드 매칭 (확정)
    for age, keywords in AGE_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return age

    # 2단계: 브랜드 매핑
    if brand:
        brand_map = _load_brand_age_map()
        age = brand_map.get(brand.lower())
        if age:
            return age

    # 3단계: 카테고리 기본 편향
    if category and category in CATEGORY_AGE_BIAS:
        return CATEGORY_AGE_BIAS[category]

    # 4단계: 가격 기반
    if price > 0 and group:
        thresholds = PRICE_AGE_THRESHOLDS.get(group)
        if thresholds:
            young_max, mid_max = thresholds
            if price <= young_max:
                return "20s"
            elif price <= mid_max:
                return "30s"
            else:
                return "40plus"

    # 미분류 → 30s 기본값
    return "30s"


def classify_item(item: dict) -> dict:
    """상품 1건 분류. category, group, gender, formality, age_group 반환."""
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
    age_group = classify_age_group(item, category, group)

    return {
        "category": category,
        "group": group,
        "gender": gender,
        "formality": formality,
        "age_group": age_group,
    }


def process_normalized_files() -> dict:
    """normalized JSON 파일들에 분류 결과를 write-back한다."""
    files = sorted(glob.glob("data/normalized/*.json"))
    stats = {"total": 0, "classified": 0, "non_fashion": 0, "age_dist": {"20s": 0, "30s": 0, "40plus": 0}}

    for filepath in files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        tone_id = data["tone_id"]
        updated_items = []

        for item in data["items"]:
            stats["total"] += 1
            raw_cat2 = item.get("raw_category2", "")

            if raw_cat2 and raw_cat2 not in FASHION_CATEGORIES:
                stats["non_fashion"] += 1
                continue

            name_lower = item.get("name", "").lower()
            if any(kw in name_lower for kw in EXCLUDE_KEYWORDS):
                stats["non_fashion"] += 1
                continue

            result = classify_item(item)
            item["category"] = result["category"]
            item["gender"] = result["gender"]
            item["formality"] = result["formality"]
            item["age_group"] = result["age_group"]

            if result["category"]:
                stats["classified"] += 1

            stats["age_dist"][result["age_group"]] += 1
            updated_items.append(item)

        data["items"] = updated_items
        data["item_count"] = len(updated_items)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  {tone_id}: {len(updated_items)}건")

    return stats


async def update_db():
    """DB products 테이블에 category, gender, formality, age_group 업데이트."""
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url, statement_cache_size=0)

    try:
        # age_group 컬럼 추가 (없으면)
        await conn.execute("""
            DO $$ BEGIN
                ALTER TABLE products ADD COLUMN age_group VARCHAR(10);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_products_age_group ON products(age_group)")

        files = sorted(glob.glob("data/normalized/*.json"))
        valid_ids = set()
        updates = []

        for filepath in files:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            for item in data["items"]:
                pid = item["product_id"]
                valid_ids.add(pid)
                updates.append((
                    item.get("category"),
                    item.get("gender"),
                    item.get("formality"),
                    item.get("age_group"),
                    pid,
                ))

        # 비패션 상품 DB에서 삭제
        deleted = await conn.execute(
            "DELETE FROM products WHERE id != ALL($1::text[])",
            list(valid_ids),
        )
        print(f"\n  비패션 상품 삭제: {deleted}")

        # 일괄 업데이트
        BATCH = 500
        for i in range(0, len(updates), BATCH):
            batch = updates[i:i + BATCH]
            await conn.executemany(
                "UPDATE products SET category=$1, gender=$2, formality=$3, age_group=$4 WHERE id=$5",
                batch,
            )

        # 검증
        total = await conn.fetchval("SELECT count(*) FROM products")
        cat_count = await conn.fetchval("SELECT count(*) FROM products WHERE category IS NOT NULL")
        print(f"  DB: {cat_count}/{total} 상품에 category 설정됨")

        rows = await conn.fetch(
            "SELECT age_group, count(*) as cnt FROM products GROUP BY age_group ORDER BY cnt DESC"
        )
        print("\n  연령대 분포:")
        for r in rows:
            print(f"    {r['age_group']}: {r['cnt']}")

    finally:
        await conn.close()


async def main():
    print("[1/2] Normalized JSON 분류 + write-back...")
    stats = process_normalized_files()
    print(f"\n  총 {stats['total']}건 → 분류 {stats['classified']}건, 비패션 제거 {stats['non_fashion']}건")
    print(f"  연령대: 20s={stats['age_dist']['20s']}, 30s={stats['age_dist']['30s']}, 40plus={stats['age_dist']['40plus']}")

    print("\n[2/2] DB 업데이트...")
    await update_db()

    print("\n✅ 상품 분류 완료")


if __name__ == "__main__":
    asyncio.run(main())
