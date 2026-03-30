"""
raw JSON → NormalizedProduct 변환 스크립트.

HTML 태그 제거, 브랜드명 추출, 중복 제거를 수행한다.
카테고리 분류(Task 1.8)와 색상 추출(Task 1.7)은 별도 단계에서 처리.

Usage:
    python -m scripts.rebuild_from_tones
    python -m scripts.rebuild_from_tones --tones spring_warm_light summer_cool_soft
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
NORMALIZED_DIR = DATA_DIR / "normalized"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

HTML_TAG_RE = re.compile(r"<[^>]+>")


def load_brand_whitelist() -> set[str]:
    """brand_whitelist.json을 로드하여 소문자 세트로 반환한다."""
    path = DATA_DIR / "brand_whitelist.json"
    with open(path, encoding="utf-8") as f:
        brands = json.load(f)
    return {b.lower() for b in brands}


def strip_html(text: str) -> str:
    """HTML 태그를 제거한다."""
    return HTML_TAG_RE.sub("", text).strip()


def extract_brand(item: dict, whitelist: set[str]) -> str | None:
    """브랜드명을 추출한다.

    우선순위:
    1. API의 brand 필드 (비어있지 않으면)
    2. title 첫 단어가 화이트리스트에 있으면 사용
    3. maker 필드
    4. None
    """
    api_brand = item.get("brand", "").strip()
    if api_brand:
        return api_brand

    title = strip_html(item.get("title", ""))
    if title:
        first_token = title.split()[0] if title.split() else ""
        if first_token.lower() in whitelist:
            return first_token
        for n in (3, 2):
            tokens = title.split()[:n]
            candidate = " ".join(tokens)
            if candidate.lower() in whitelist:
                return candidate

    maker = item.get("maker", "").strip()
    if maker:
        return maker

    return None


def normalize_item(item: dict, tone_id: str, whitelist: set[str]) -> dict:
    """raw API 아이템을 NormalizedProduct 형식으로 변환한다."""
    name = strip_html(item.get("title", ""))
    brand = extract_brand(item, whitelist)

    lprice = item.get("lprice", "")
    price = int(lprice) if lprice and lprice.isdigit() else None

    return {
        "product_id": item.get("productId", ""),
        "name": name,
        "brand": brand,
        "category": None,
        "color_hex": None,
        "tone_id": tone_id,
        "price": price,
        "mall_name": item.get("mallName", ""),
        "mall_url": item.get("link", ""),
        "image_url": item.get("image", ""),
        "tags": [],
        "raw_category1": item.get("category1", ""),
        "raw_category2": item.get("category2", ""),
        "raw_category3": item.get("category3", ""),
        "raw_category4": item.get("category4", ""),
    }


def process_tone(
    tone_id: str, whitelist: set[str], global_seen: set[str]
) -> dict:
    """하나의 톤 raw JSON을 정규화한다.

    global_seen: 크로스-톤 중복 제거를 위한 글로벌 product_id 세트.
    """
    raw_path = RAW_DIR / f"{tone_id}.json"
    if not raw_path.exists():
        logger.warning("[%s] raw 파일 없음: %s", tone_id, raw_path)
        return {"tone_id": tone_id, "item_count": 0, "items": []}

    with open(raw_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    raw_items = raw_data.get("items", [])
    normalized: list[dict] = []

    for item in raw_items:
        pid = item.get("productId", "")
        if not pid or pid in global_seen:
            continue

        product = normalize_item(item, tone_id, whitelist)
        if not product["name"]:
            continue
        global_seen.add(pid)
        normalized.append(product)

    dedup_removed = len(raw_items) - len(normalized)
    logger.info(
        "[%s] 정규화 완료 — raw %d건 → 정규화 %d건 (중복/빈값 제거 %d건)",
        tone_id, len(raw_items), len(normalized), dedup_removed,
    )

    return {
        "tone_id": tone_id,
        "normalized_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "raw_count": len(raw_items),
        "item_count": len(normalized),
        "duplicates_removed": dedup_removed,
        "items": normalized,
    }


def save_normalized(tone_id: str, data: dict) -> Path:
    """정규화 결과를 JSON으로 저장한다."""
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    filepath = NORMALIZED_DIR / f"{tone_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("[%s] 저장: %s (%d건)", tone_id, filepath, data["item_count"])
    return filepath


def get_available_tones() -> list[str]:
    """raw 디렉토리에서 사용 가능한 톤 목록을 반환한다."""
    return sorted(p.stem for p in RAW_DIR.glob("*.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description="raw JSON → NormalizedProduct 변환")
    parser.add_argument(
        "--tones",
        nargs="+",
        help="처리할 톤 ID 목록",
    )
    args = parser.parse_args()

    whitelist = load_brand_whitelist()
    logger.info("브랜드 화이트리스트: %d개 로드", len(whitelist))

    tones = args.tones if args.tones else get_available_tones()
    logger.info("처리 대상: %d개 톤", len(tones))

    total_raw = 0
    total_normalized = 0
    global_seen: set[str] = set()

    for tone_id in tones:
        result = process_tone(tone_id, whitelist, global_seen)
        if result["item_count"] > 0:
            save_normalized(tone_id, result)
        total_raw += result.get("raw_count", 0)
        total_normalized += result["item_count"]

    logger.info(
        "전체 완료 — raw %d건 → 정규화 %d건",
        total_raw, total_normalized,
    )


if __name__ == "__main__":
    main()
