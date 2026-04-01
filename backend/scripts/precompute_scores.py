"""코디 5축 스코어 프리컴퓨팅 스크립트.

기획서 섹션 5.5 구현.
generated_outfits.json의 모든 코디에 대해 기본 5축 스코어를 사전 계산하여
outfits.scores JSONB에 저장한다.

프리컴퓨팅 기준:
- PCF: 코디의 설계 톤(tags[0])을 user_tone_id로 가정
- OF: 코디의 designed_tpo를 user tpo로 가정
- CH: 아이템 색상 조합 (사용자 무관)
- PE: 코디 총액 ± 50% 범위를 기본 예산으로 가정
- SF: 카테고리 + 실루엣 (사용자 무관)

런타임에는 실제 사용자 프로필로 개인화 보정만 적용.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.scoring import (
    COMPATIBLE_TONES,
    calculate_pcf,
    calculate_of,
    calculate_ch,
    calculate_pe,
    calculate_sf,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NORMALIZED_DIR = DATA_DIR / "normalized"
OUTFITS_PATH = DATA_DIR / "generated_outfits.json"

CATEGORY_TO_GROUP: dict[str, str] = {
    "티셔츠": "top", "셔츠": "top", "블라우스": "top", "니트": "top",
    "맨투맨": "top", "후드": "top", "탱크톱": "top", "크롭탑": "top", "폴로": "top",
    "자켓": "outer", "코트": "outer", "패딩": "outer", "가디건": "outer",
    "점퍼": "outer", "블레이저": "outer", "야상": "outer", "바람막이": "outer", "조끼": "outer",
    "청바지": "bottom", "슬랙스": "bottom", "면바지": "bottom", "반바지": "bottom",
    "스커트": "bottom", "와이드팬츠": "bottom", "레깅스": "bottom",
    "조거팬츠": "bottom", "숏팬츠": "bottom", "치노": "bottom",
    "원피스": "onepiece", "점프수트": "onepiece",
    "스니커즈": "shoes", "로퍼": "shoes", "부츠": "shoes", "샌들": "shoes",
    "힐": "shoes", "플랫슈즈": "shoes", "슬리퍼": "shoes", "더비": "shoes",
    "가방": "bag", "백팩": "bag", "토트백": "bag", "크로스백": "bag",
    "모자": "acc", "머플러": "acc", "벨트": "acc", "주얼리": "acc",
    "시계": "acc", "선글라스": "acc", "스카프": "acc", "액세서리": "acc",
}


def _tone_level_pcf(item_tone_ids: list[str], user_tone_id: str) -> float:
    """color_hex 없이 tone_id만으로 PCF를 계산한다.

    동일 톤: 100, 호환 톤: 95, 같은 시즌: 70, 다른 시즌: 30
    """
    if not item_tone_ids:
        return 0.0

    compatible = COMPATIBLE_TONES.get(user_tone_id, set())
    user_season = user_tone_id.split("_")[0] if user_tone_id else ""

    scores: list[float] = []
    for tone in item_tone_ids:
        if tone == user_tone_id:
            scores.append(100.0)
        elif tone in compatible:
            scores.append(95.0)
        elif tone.split("_")[0] == user_season:
            scores.append(70.0)
        else:
            scores.append(30.0)

    return round(sum(scores) / len(scores), 2)


def load_product_index() -> dict[str, dict]:
    """normalized 데이터에서 product_id → 상품 정보 인덱스를 구축한다."""
    index: dict[str, dict] = {}
    for tone_file in NORMALIZED_DIR.glob("*.json"):
        with open(tone_file, encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("items", []):
            pid = item.get("product_id")
            if pid:
                index[pid] = item
    logger.info(f"상품 인덱스 구축: {len(index)}개")
    return index


def extract_tone_from_tags(tags: list[str] | None) -> str | None:
    """코디 태그에서 톤 ID를 추출한다."""
    if not tags:
        return None
    tone_prefixes = ("spring_", "summer_", "autumn_", "winter_")
    for tag in tags:
        if any(tag.startswith(p) for p in tone_prefixes):
            return tag
    return None


def compute_scores(outfit: dict, product_index: dict) -> dict[str, float]:
    """단일 코디의 5축 스코어를 계산한다."""
    items_snapshot = outfit.get("items_snapshot", [])
    if not items_snapshot:
        return {"pcf": 0.0, "of": 0.0, "ch": 50.0, "pe": 0.0, "sf": 0.0}

    # 아이템 데이터 수집 (normalized 데이터에서 보강)
    tone_ids: list[str] = []
    hex_colors: list[str] = []
    categories: list[str] = []
    top_silhouette: str | None = None
    bottom_silhouette: str | None = None

    for snap in items_snapshot:
        pid = snap.get("product_id")
        normalized = product_index.get(pid, {})

        tone_id = normalized.get("tone_id")
        color_hex = normalized.get("color_hex")
        category = snap.get("category") or normalized.get("category")

        if tone_id:
            tone_ids.append(tone_id)
        if color_hex:
            hex_colors.append(color_hex)
        if category:
            categories.append(category)
            group = CATEGORY_TO_GROUP.get(category, "")
            silhouette = normalized.get("silhouette")
            if silhouette:
                if group in ("top", "outer") and top_silhouette is None:
                    top_silhouette = silhouette
                elif group == "bottom" and bottom_silhouette is None:
                    bottom_silhouette = silhouette

    # PCF: 코디 설계 톤 기준
    # color_hex가 있으면 정밀 계산, 없으면 tone_id 레벨 매칭만
    user_tone = extract_tone_from_tags(outfit.get("tags"))
    pcf = 0.0
    if user_tone and tone_ids:
        if hex_colors and len(tone_ids) == len(hex_colors):
            try:
                pcf = calculate_pcf(tone_ids, hex_colors, user_tone)
            except Exception as e:
                logger.debug(f"PCF 정밀 계산 실패 ({outfit.get('id')}): {e}")
                pcf = _tone_level_pcf(tone_ids, user_tone)
        else:
            pcf = _tone_level_pcf(tone_ids, user_tone)

    # OF: 코디 설계 TPO 기준
    designed_tpo = outfit.get("designed_tpo")
    outfit_tags = outfit.get("tags", [])
    user_tpo_list = [designed_tpo] if designed_tpo else []
    of = calculate_of(outfit_tags, user_tpo_list)

    # CH: 아이템 색상 조합
    ch = calculate_ch(hex_colors) if len(hex_colors) >= 2 else 50.0

    # PE: 코디 총액 기준 기본 예산 (총액 ± 50%)
    total_price = outfit.get("total_price", 0) or 0
    if total_price > 0:
        budget_min = max(1, int(total_price * 0.5))
        budget_max = int(total_price * 1.5)
        pe = calculate_pe(total_price, budget_min, budget_max)
    else:
        pe = 0.0

    # SF: 카테고리 + 실루엣
    sf = calculate_sf(categories, top_silhouette, bottom_silhouette)

    return {
        "pcf": pcf,
        "of": of,
        "ch": ch,
        "pe": pe,
        "sf": sf,
    }


def main():
    parser = argparse.ArgumentParser(description="코디 5축 스코어 프리컴퓨팅")
    parser.add_argument("--dry-run", action="store_true", help="파일 저장 없이 실행")
    args = parser.parse_args()

    logger.info("스코어 프리컴퓨팅 시작")
    start = time.time()

    # 1. 상품 인덱스 구축
    product_index = load_product_index()

    # 2. 코디 로드
    with open(OUTFITS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    outfits = data.get("outfits", [])
    logger.info(f"코디 {len(outfits)}개 로드")

    # 3. 스코어 계산
    computed = 0
    score_sums: dict[str, float] = {"pcf": 0, "of": 0, "ch": 0, "pe": 0, "sf": 0}

    for outfit in outfits:
        scores = compute_scores(outfit, product_index)
        outfit["scores"] = scores
        computed += 1

        for axis in score_sums:
            score_sums[axis] += scores[axis]

    # 4. 통계 로그
    elapsed = time.time() - start
    logger.info(f"계산 완료: {computed}개 ({elapsed:.1f}s)")

    if computed > 0:
        logger.info("평균 스코어:")
        for axis in ["pcf", "of", "ch", "pe", "sf"]:
            avg = score_sums[axis] / computed
            logger.info(f"  {axis.upper()}: {avg:.1f}")

    # 5. 저장 (임시 파일 → 원자적 교체)
    if args.dry_run:
        logger.info("dry-run 모드: 파일 저장 건너뜀")
    else:
        import os
        import tempfile
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=OUTFITS_PATH.parent, suffix=".tmp",
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, OUTFITS_PATH)
            logger.info(f"저장 완료: {OUTFITS_PATH}")
        except Exception:
            os.unlink(tmp_path)
            raise


if __name__ == "__main__":
    main()
