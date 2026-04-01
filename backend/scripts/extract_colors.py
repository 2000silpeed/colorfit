"""normalized 상품의 이미지에서 색상을 추출하고 톤을 매핑한다.

Task 1.7: 이미지 색상 추출 + 톤 매핑 전처리 스크립트.

Usage:
    python -m scripts.extract_colors
    python -m scripts.extract_colors --tones spring_warm_light summer_cool_soft
    python -m scripts.extract_colors --limit 100  # 테스트용: 톤당 100개만
    python -m scripts.extract_colors --dry-run     # 저장 없이 미리보기
"""

import argparse
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

from app.services.color_extractor import extract_colors_from_url
from app.services.color_matcher import TonePalette

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
NORMALIZED_DIR = DATA_DIR / "normalized"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BATCH_LOG_INTERVAL = 500
MAX_WORKERS = 20


def get_available_tones() -> list[str]:
    """normalized 디렉토리에서 사용 가능한 톤 목록을 반환한다."""
    return sorted(p.stem for p in NORMALIZED_DIR.glob("*.json"))


def _extract_single(
    image_url: str,
    palette: TonePalette,
) -> dict | None:
    """단일 아이템의 색상을 추출한다. 스레드별 독립 HTTP 요청."""
    if not image_url:
        return None
    colors = extract_colors_from_url(image_url, n_colors=3, client=None)
    if not colors:
        return None
    tone_id_mapped, primary_hex = palette.match_dominant_colors(colors)
    return {"color_hex": primary_hex, "tone_id": tone_id_mapped}


BATCH_SIZE = 200
SAVE_INTERVAL = 2000


def process_tone(
    tone_id: str,
    palette: TonePalette,
    limit: int | None = None,
    dry_run: bool = False,
    max_workers: int = MAX_WORKERS,
) -> dict:
    """하나의 톤 파일에 대해 색상 추출 + 톤 매핑을 수행한다."""
    filepath = NORMALIZED_DIR / f"{tone_id}.json"
    if not filepath.exists():
        logger.warning("[%s] normalized 파일 없음", tone_id)
        return {"processed": 0, "skipped": 0, "failed": 0}

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    total = len(items)
    if limit:
        items = items[:limit]

    skipped = 0
    to_process: list[tuple[int, dict]] = []
    for i, item in enumerate(items):
        if item.get("color_hex"):
            skipped += 1
        elif not item.get("image_url"):
            pass
        else:
            to_process.append((i, item))

    logger.info("[%s] 처리 대상 %d건 (스킵 %d건)", tone_id, len(to_process), skipped)

    processed = 0
    failed = 0
    last_save = 0

    for batch_start in range(0, len(to_process), BATCH_SIZE):
        batch = to_process[batch_start:batch_start + BATCH_SIZE]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(_extract_single, item["image_url"], palette): item
                for _, item in batch
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                except Exception:
                    failed += 1
                    continue

                if result is None:
                    failed += 1
                else:
                    item["color_hex"] = result["color_hex"]
                    item["tone_id"] = result["tone_id"]
                    processed += 1

        done_count = batch_start + len(batch)
        logger.info(
            "[%s] 진행: %d/%d (성공 %d, 실패 %d)",
            tone_id, done_count, len(to_process), processed, failed,
        )

        if not dry_run and (processed - last_save) >= SAVE_INTERVAL:
            data["color_extracted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            data["color_stats"] = {
                "processed": processed, "skipped": skipped, "failed": failed,
            }
            tmp = filepath.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp.replace(filepath)
            last_save = processed
            logger.info("[%s] 중간 저장 (%d건)", tone_id, processed)

    logger.info(
        "[%s] 완료 — 전체 %d건 중 처리 %d / 스킵 %d / 실패 %d",
        tone_id, total, processed, skipped, failed,
    )

    if not dry_run and processed > last_save:
        data["color_extracted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        data["color_stats"] = {
            "processed": processed, "skipped": skipped, "failed": failed,
        }
        tmp = filepath.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(filepath)
        logger.info("[%s] 최종 저장 완료", tone_id)

    return {"processed": processed, "skipped": skipped, "failed": failed}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="이미지 색상 추출 + 12톤 매핑 전처리"
    )
    parser.add_argument("--tones", nargs="+", help="처리할 톤 ID 목록")
    parser.add_argument("--limit", type=int, help="톤당 최대 처리 수 (테스트용)")
    parser.add_argument("--dry-run", action="store_true", help="저장 없이 미리보기")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="동시 처리 스레드 수")
    args = parser.parse_args()

    palette = TonePalette()
    tones = args.tones if args.tones else get_available_tones()
    logger.info(
        "처리 대상: %d개 톤 (limit=%s, dry_run=%s, workers=%d)",
        len(tones), args.limit, args.dry_run, args.workers,
    )

    total_stats = {"processed": 0, "skipped": 0, "failed": 0}

    for tone_id in tones:
        stats = process_tone(tone_id, palette, args.limit, args.dry_run, args.workers)
        for k in total_stats:
            total_stats[k] += stats[k]

    logger.info(
        "전체 완료 — 처리 %d / 스킵 %d / 실패 %d",
        total_stats["processed"], total_stats["skipped"], total_stats["failed"],
    )


if __name__ == "__main__":
    main()
