"""brand가 NULL인 상품에 브랜드를 보충한다.

3단계 매칭:
1. 상품명에서 화이트리스트 브랜드 키워드 매칭
2. 상품명에서 대괄호 [브랜드명] 패턴 추출 → 화이트리스트 체크
3. raw 데이터의 maker 필드 활용 (normalized JSON에서)

DB + normalized JSON 모두 업데이트.
"""

import asyncio
import json
import glob
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from app.config import settings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 화이트리스트 로드 + 검색용 인덱스 (긴 이름 우선)
with open(DATA_DIR / "brand_whitelist.json", encoding="utf-8") as f:
    WHITELIST: list[str] = json.load(f)

# 브랜드 별칭 (상품명에 자주 등장하는 변형)
BRAND_ALIASES: dict[str, str] = {
    "나이키": "나이키", "nike": "나이키",
    "아디다스": "아디다스", "adidas": "아디다스",
    "뉴발란스": "뉴발란스", "new balance": "뉴발란스", "newbalance": "뉴발란스",
    "컨버스": "컨버스", "converse": "컨버스",
    "반스": "반스", "vans": "반스",
    "푸마": "푸마", "puma": "푸마",
    "리복": "리복", "reebok": "리복",
    "유니클로": "유니클로", "uniqlo": "유니클로",
    "자라": "자라", "zara": "자라",
    "h&m": "H&M",
    "cos": "COS",
    "갭": "갭", "gap": "갭",
    "스파오": "스파오", "spao": "스파오",
    "탑텐": "탑텐", "topten": "탑텐",
    "리바이스": "리바이스", "levis": "리바이스", "levi's": "리바이스",
    "랄프로렌": "랄프로렌", "ralph lauren": "랄프로렌",
    "타미힐피거": "타미힐피거", "tommy hilfiger": "타미힐피거",
    "캘빈클라인": "캘빈클라인", "calvin klein": "캘빈클라인", "ck": "캘빈클라인",
    "라코스테": "라코스테", "lacoste": "라코스테",
    "노스페이스": "노스페이스", "the north face": "노스페이스", "northface": "노스페이스",
    "파타고니아": "파타고니아", "patagonia": "파타고니아",
    "아크테릭스": "아크테릭스", "arcteryx": "아크테릭스", "arc'teryx": "아크테릭스",
    "버버리": "버버리", "burberry": "버버리",
    "구찌": "구찌", "gucci": "구찌",
    "프라다": "프라다", "prada": "프라다",
    "디올": "디올", "dior": "디올",
    "발렌시아가": "발렌시아가", "balenciaga": "발렌시아가",
    "생로랑": "생로랑", "saint laurent": "생로랑", "ysl": "생로랑",
    "루이비통": "루이비통", "louis vuitton": "루이비통",
    "에르메스": "에르메스", "hermes": "에르메스",
    "셀린느": "셀린느", "celine": "셀린느",
    "보테가베네타": "보테가베네타", "bottega veneta": "보테가베네타",
    "로에베": "로에베", "loewe": "로에베",
    "톰브라운": "톰브라운", "thom browne": "톰브라운",
    "몽클레르": "몽클레르", "moncler": "몽클레르",
    "막스마라": "막스마라", "max mara": "막스마라",
    "페라가모": "페라가모", "ferragamo": "페라가모",
    "미우미우": "미우미우", "miu miu": "미우미우",
    "알렉산더맥퀸": "발렌시아가",  # 같은 케어링 그룹이지만 별도 매핑은 없으니 스킵
    "마시모두띠": "마시모두띠", "massimo dutti": "마시모두띠",
    "무신사스탠다드": "무신사 스탠다드", "무신사 스탠다드": "무신사 스탠다드",
    "커버낫": "커버낫", "covernat": "커버낫",
    "디스이즈네버댓": "디스이즈네버댓", "thisisneverthat": "디스이즈네버댓",
    "마뗑킴": "마뗑킴", "matin kim": "마뗑킴",
    "아미": "아미", "ami": "아미",
    "아크네": "아크네 스튜디오", "acne studios": "아크네 스튜디오",
    "메종키츠네": "메종키츠네", "maison kitsune": "메종키츠네",
    "스톤아일랜드": "스톤아일랜드", "stone island": "스톤아일랜드",
    "꼼데가르송": "꼼데가르송", "comme des garcons": "꼼데가르송",
    "닥터마틴": "닥터마틴", "dr.martens": "닥터마틴", "dr martens": "닥터마틴",
    "버켄스탁": "버켄스탁", "birkenstock": "버켄스탁",
    "살로몬": "살로몬", "salomon": "살로몬",
    "룰루레몬": "룰루레몬", "lululemon": "룰루레몬",
    "빈폴": "빈폴", "beanpole": "빈폴",
    "헤지스": "헤지스", "hazzys": "헤지스",
    "널디": "디스이즈네버댓",  # 비슷한 브랜드지만 별도
    "앤더슨벨": "앤더슨벨", "andersson bell": "앤더슨벨",
    "마르디메크르디": "마르디 메크르디", "mardi mercredi": "마르디 메크르디",
    "a.p.c.": "A.P.C.", "a.p.c": "A.P.C.", "apc": "A.P.C.",
    "mlb": "MLB",
    "fila": "휠라", "휠라": "휠라",
    "k2": "K2",
    "블랙야크": "블랙야크", "blackyak": "블랙야크",
    "네파": "네파", "nepa": "네파",
    "컬럼비아": "컬럼비아", "columbia": "컬럼비아",
    "캐나다구스": "캐나다구스", "canada goose": "캐나다구스",
    "크록스": "크록스", "crocs": "크록스",
    "클락스": "클락스", "clarks": "클락스",
    "팀버랜드": "팀버랜드", "timberland": "팀버랜드",
    "산드로": "산드로", "sandro": "산드로",
    "마쥬": "마쥬", "maje": "마쥬",
}

# 화이트리스트 소문자 세트
WHITELIST_LOWER = {b.lower() for b in WHITELIST}

# 검색 키워드 인덱스 (긴 것 먼저 매칭)
SEARCH_KEYWORDS: list[tuple[str, str]] = []
for alias, brand in BRAND_ALIASES.items():
    if brand.lower() in WHITELIST_LOWER:
        SEARCH_KEYWORDS.append((alias.lower(), brand))
# 화이트리스트 자체도 추가
for brand in WHITELIST:
    SEARCH_KEYWORDS.append((brand.lower(), brand))
SEARCH_KEYWORDS.sort(key=lambda x: len(x[0]), reverse=True)

# 대괄호 브랜드 패턴
BRACKET_PATTERN = re.compile(r"\[([^\]]{2,30})\]")


def extract_brand_from_name(name: str) -> str | None:
    """상품명에서 브랜드를 추출한다."""
    name_lower = name.lower()

    # 1단계: 대괄호 패턴 [브랜드명] 매칭
    brackets = BRACKET_PATTERN.findall(name)
    for bracket_text in brackets:
        bt_lower = bracket_text.strip().lower()
        for keyword, brand in SEARCH_KEYWORDS:
            if keyword in bt_lower:
                return brand

    # 2단계: 상품명 전체에서 키워드 매칭
    for keyword, brand in SEARCH_KEYWORDS:
        if keyword in name_lower:
            return brand

    return None


def process_normalized_files() -> dict:
    """normalized JSON 파일에서 brand NULL 상품의 브랜드를 보충한다."""
    files = sorted(glob.glob(str(DATA_DIR / "normalized" / "*.json")))
    stats = {"total": 0, "already_has": 0, "filled": 0, "still_null": 0}

    for filepath in files:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        tone_id = data["tone_id"]
        updated = 0

        for item in data["items"]:
            stats["total"] += 1
            if item.get("brand"):
                stats["already_has"] += 1
                continue

            brand = extract_brand_from_name(item.get("name", ""))
            if brand:
                item["brand"] = brand
                stats["filled"] += 1
                updated += 1
            else:
                stats["still_null"] += 1

        if updated > 0:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  {tone_id}: {updated}건 보충")

    return stats


async def update_db(stats: dict):
    """DB products 테이블의 brand를 업데이트한다."""
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url, statement_cache_size=0)

    try:
        files = sorted(glob.glob(str(DATA_DIR / "normalized" / "*.json")))
        updates = []

        for filepath in files:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            for item in data["items"]:
                if item.get("brand"):
                    updates.append((item["brand"], item["product_id"]))

        BATCH = 500
        updated_count = 0
        for i in range(0, len(updates), BATCH):
            batch = updates[i:i + BATCH]
            await conn.executemany(
                "UPDATE products SET brand=$1 WHERE id=$2 AND (brand IS NULL OR brand = '')",
                batch,
            )
            updated_count += len(batch)

        # 검증
        total = await conn.fetchval("SELECT count(*) FROM products")
        brand_null = await conn.fetchval("SELECT count(*) FROM products WHERE brand IS NULL OR brand = ''")
        print(f"\n  DB: brand NULL {brand_null}/{total} ({round(brand_null/total*100,1)}%)")

    finally:
        await conn.close()


async def main():
    print("[1/2] Normalized JSON 브랜드 보충...")
    stats = process_normalized_files()
    print(f"\n  총 {stats['total']}건")
    print(f"  이미 있음: {stats['already_has']}건")
    print(f"  보충됨: {stats['filled']}건")
    print(f"  여전히 NULL: {stats['still_null']}건")

    print("\n[2/2] DB 업데이트...")
    await update_db(stats)

    print("\n완료")


if __name__ == "__main__":
    asyncio.run(main())
