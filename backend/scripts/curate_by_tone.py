"""
네이버 쇼핑 API 기반 톤별 상품 수집 스크립트.

Usage:
    python -m scripts.curate_by_tone --tones spring_warm_light summer_cool_soft
    python -m scripts.curate_by_tone --all
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"
MAX_DISPLAY = 100
MAX_START = 1000
RATE_LIMIT_PER_SEC = 10
REQUEST_INTERVAL = 1.0 / RATE_LIMIT_PER_SEC

TONE_IDS = [
    "spring_warm_light",
    "spring_warm_bright",
    "spring_warm_vivid",
    "summer_cool_light",
    "summer_cool_soft",  # 기획서: summer_cool_soft → mute 계열
    "summer_cool_bright",
    "summer_cool_mute",
    "autumn_warm_mute",
    "autumn_warm_strong",
    "autumn_warm_deep",
    "winter_cool_deep",
    "winter_cool_strong",
    "winter_cool_vivid",
]

TONE_QUERIES_PATH = DATA_DIR / "tone_queries.json"


def _load_tone_queries() -> dict[str, dict[str, list[str]]]:
    """tone_queries.json에서 톤별 카테고리별 쿼리를 로드한다."""
    with open(TONE_QUERIES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_meta", None)
    return data


TONE_QUERIES: dict[str, dict[str, list[str]]] = _load_tone_queries()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_queries(tone_id: str) -> list[str]:
    """톤 ID에 해당하는 검색 쿼리 리스트를 생성한다."""
    tone_data = TONE_QUERIES.get(tone_id, {})
    queries: list[str] = []
    for category_queries in tone_data.values():
        queries.extend(category_queries)
    return queries


def _get_credentials() -> tuple[str, str]:
    """환경변수에서 네이버 API 인증 정보를 가져온다. .env 파일도 로드한다."""
    load_dotenv(BASE_DIR / ".env")
    client_id = os.environ.get("NAVER_CLIENT_ID", "")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        logger.error("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다.")
        sys.exit(1)
    return client_id, client_secret


async def search_products(
    client: httpx.AsyncClient,
    query: str,
    display: int = MAX_DISPLAY,
    start: int = 1,
    *,
    client_id: str,
    client_secret: str,
) -> dict:
    """네이버 쇼핑 API를 호출하여 상품을 검색한다."""
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": min(display, MAX_DISPLAY),
        "start": min(start, MAX_START),
        "sort": "sim",
    }
    response = await client.get(
        NAVER_SEARCH_URL, headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


async def collect_for_query(
    client: httpx.AsyncClient,
    query: str,
    *,
    client_id: str,
    client_secret: str,
    max_pages: int = 3,
) -> list[dict]:
    """하나의 쿼리에 대해 페이지네이션하며 상품을 수집한다."""
    all_items: list[dict] = []
    page = 0
    while page < max_pages:
        start = page * MAX_DISPLAY + 1
        if start > MAX_START:
            break
        try:
            data = await search_products(
                client,
                query,
                display=MAX_DISPLAY,
                start=start,
                client_id=client_id,
                client_secret=client_secret,
            )
            items = data.get("items", [])
            if not items:
                await asyncio.sleep(REQUEST_INTERVAL)
                break
            all_items.extend(items)
            logger.debug("  %s (start=%d): %d건", query, start, len(items))
            await asyncio.sleep(REQUEST_INTERVAL)
            page += 1
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = _backoff_wait(page)
                logger.warning("Rate limit 초과, %0.1f초 대기 후 재시도 (start=%d)", wait, start)
                await asyncio.sleep(wait)
                continue
            logger.error("API 에러 (query=%s, start=%d): %s", query, start, e)
            break
    return all_items


def _backoff_wait(attempt: int) -> float:
    """Exponential backoff: 1s → 2s → 4s → ..."""
    return min(2 ** attempt, 16)


async def collect_for_tone(tone_id: str) -> dict:
    """하나의 톤에 대해 전체 쿼리를 실행하고 결과를 모은다."""
    client_id, client_secret = _get_credentials()
    queries = build_queries(tone_id)
    logger.info("[%s] 수집 시작 — 쿼리 %d개", tone_id, len(queries))

    all_items: list[dict] = []
    api_call_count = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, query in enumerate(queries):
            items = await collect_for_query(
                client,
                query,
                client_id=client_id,
                client_secret=client_secret,
            )
            all_items.extend(items)
            api_call_count += (len(items) // MAX_DISPLAY) + 1
            if (i + 1) % 20 == 0:
                logger.info(
                    "[%s] 진행: %d/%d 쿼리, 누적 %d건",
                    tone_id, i + 1, len(queries), len(all_items),
                )

    result = {
        "tone_id": tone_id,
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "query_count": len(queries),
        "item_count": len(all_items),
        "api_call_count": api_call_count,
        "items": all_items,
    }
    logger.info(
        "[%s] 수집 완료 — %d건 (API 호출 %d회)",
        tone_id, len(all_items), api_call_count,
    )
    return result


def save_raw_json(tone_id: str, data: dict) -> Path:
    """수집 결과를 raw JSON으로 저장한다."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RAW_DIR / f"{tone_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("[%s] 저장: %s (%d건)", tone_id, filepath, data["item_count"])
    return filepath


async def run(tone_ids: list[str]) -> None:
    """지정된 톤들에 대해 순차적으로 수집을 실행한다."""
    for tone_id in tone_ids:
        if tone_id not in TONE_IDS:
            logger.warning("알 수 없는 톤 ID: %s (건너뜀)", tone_id)
            continue
        data = await collect_for_tone(tone_id)
        save_raw_json(tone_id, data)


def main() -> None:
    parser = argparse.ArgumentParser(description="네이버 쇼핑 API 톤별 상품 수집")
    parser.add_argument(
        "--tones",
        nargs="+",
        help="수집할 톤 ID 목록 (예: spring_warm_light summer_cool_soft)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="전체 13톤 수집",
    )
    args = parser.parse_args()

    if args.all:
        targets = TONE_IDS
    elif args.tones:
        targets = args.tones
    else:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run(targets))


if __name__ == "__main__":
    main()
