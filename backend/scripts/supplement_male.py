"""남성 상품 보충 수집 스크립트.

tone_queries.json의 *_male 카테고리 쿼리만 실행하여
기존 raw 데이터에 병합하고, normalized 데이터를 재생성한다.

Usage:
    python scripts/supplement_male.py --all
    python scripts/supplement_male.py --tones spring_warm_light summer_cool_soft
    python scripts/supplement_male.py --all --skip-normalize  # raw만 수집
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.curate_by_tone import (
    TONE_IDS,
    collect_for_query,
    _get_credentials,
)
from scripts.rebuild_from_tones import (
    load_brand_whitelist,
    process_tone,
    save_normalized,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
TONE_QUERIES_PATH = DATA_DIR / "tone_queries.json"

MALE_CATEGORIES = ["top_male", "bottom_male", "outer_male", "shoes_male"]


def load_male_queries() -> dict[str, list[str]]:
    """톤별 남성 쿼리만 로드한다."""
    with open(TONE_QUERIES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for tone_id in TONE_IDS:
        tone_data = data.get(tone_id, {})
        queries = []
        for cat in MALE_CATEGORIES:
            queries.extend(tone_data.get(cat, []))
        if queries:
            result[tone_id] = queries
    return result


async def collect_male_items(tone_id: str, queries: list[str]) -> list[dict]:
    """남성 쿼리만 실행하여 아이템을 수집한다."""
    import httpx
    client_id, client_secret = _get_credentials()
    all_items: list[dict] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, query in enumerate(queries):
            items = await collect_for_query(
                client, query,
                client_id=client_id,
                client_secret=client_secret,
                max_pages=3,
            )
            all_items.extend(items)
            if (i + 1) % 10 == 0:
                logger.info("  [%s] %d/%d 쿼리 완료, 누적 %d건",
                            tone_id, i + 1, len(queries), len(all_items))

    return all_items


def merge_into_raw(tone_id: str, new_items: list[dict]) -> int:
    """기존 raw JSON에 새 아이템을 병합한다. 중복은 productId로 제거."""
    raw_path = RAW_DIR / f"{tone_id}.json"
    if raw_path.exists():
        with open(raw_path, encoding="utf-8") as f:
            existing = json.load(f)
        existing_items = existing.get("items", [])
    else:
        existing_items = []

    seen_ids = {item.get("productId") for item in existing_items}
    added = 0
    for item in new_items:
        pid = item.get("productId")
        if pid and pid not in seen_ids:
            existing_items.append(item)
            seen_ids.add(pid)
            added += 1

    result = {
        "tone_id": tone_id,
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "item_count": len(existing_items),
        "items": existing_items,
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return added


async def run(tone_ids: list[str], skip_normalize: bool = False) -> None:
    male_queries = load_male_queries()
    total_added = 0
    total_collected = 0

    for tone_id in tone_ids:
        queries = male_queries.get(tone_id, [])
        if not queries:
            logger.warning("[%s] 남성 쿼리 없음, 건너뜀", tone_id)
            continue

        logger.info("[%s] 남성 쿼리 %d개 수집 시작", tone_id, len(queries))
        items = await collect_male_items(tone_id, queries)
        total_collected += len(items)
        logger.info("[%s] 수집 완료: %d건", tone_id, len(items))

        added = merge_into_raw(tone_id, items)
        total_added += added
        logger.info("[%s] raw 병합: 신규 %d건 추가", tone_id, added)

    if not skip_normalize:
        logger.info("normalized 재생성 중...")
        whitelist = load_brand_whitelist()
        global_seen: set[str] = set()
        for tone_id in tone_ids:
            result = process_tone(tone_id, whitelist, global_seen)
            if result["item_count"] > 0:
                save_normalized(tone_id, result)
                logger.info("[%s] normalized 재생성 완료: %d건", tone_id, result["item_count"])

    logger.info("=" * 60)
    logger.info("총 수집: %d건, 신규 추가: %d건", total_collected, total_added)


def main():
    parser = argparse.ArgumentParser(description="남성 상품 보충 수집")
    parser.add_argument("--tones", nargs="+", help="수집할 톤 ID 목록")
    parser.add_argument("--all", action="store_true", help="전체 13톤 수집")
    parser.add_argument("--skip-normalize", action="store_true",
                        help="normalized 재생성 건너뛰기")
    args = parser.parse_args()

    if args.all:
        targets = TONE_IDS
    elif args.tones:
        targets = args.tones
    else:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run(targets, skip_normalize=args.skip_normalize))


if __name__ == "__main__":
    main()
