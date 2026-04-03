"""레시피 기반 코디 조합 생성 스크립트 v2.

기획서 5.3.1 구현. TPO x 무드 x 계절 레시피를 기반으로 코디 조합을 생성한다.
- 필수 카테고리 선택 → 선택 카테고리 확률적 추가 → 금지 카테고리 검증
- 계절별 금지 카테고리 오버레이 (여름에 패딩 금지 등)
- 포멀도 편차 ≤ 2, 가격 비율 3배 이내, 중복 조합 방지
- 성별 키워드 교차 검증 (상품명에 반대 성별 키워드 포함 시 제외)
- designed_tpo, designed_moods, designed_season 태그 부여
- 최소 3피스 보장 (신발 required)
"""

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.category_classifier import classify_by_keyword

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NORMALIZED_DIR = DATA_DIR / "normalized"
RECIPES_PATH = DATA_DIR / "outfit_recipes.json"
OUTPUT_PATH = DATA_DIR / "generated_outfits.json"

TONES_12 = [
    "spring_warm_light", "spring_warm_bright", "spring_warm_vivid",
    "summer_cool_light", "summer_cool_soft", "summer_cool_bright", "summer_cool_mute",
    "autumn_warm_mute", "autumn_warm_strong", "autumn_warm_deep",
    "winter_cool_deep", "winter_cool_strong",
]

DEFAULT_FORMALITY: dict[str, int] = {
    "셔츠": 4, "블라우스": 4, "니트": 3, "티셔츠": 2, "맨투맨": 2,
    "후드": 1, "크롭탑": 1, "탱크탑": 2, "폴로": 3,
    "원피스": 3,
    "코트": 4, "패딩": 2, "자켓": 4, "가디건": 3, "점퍼": 2, "조끼": 3,
    "슬랙스": 4, "청바지": 2, "스커트": 3, "와이드팬츠": 3,
    "조거팬츠": 1, "숏팬츠": 1, "레깅스": 1, "치노": 3,
    "스니커즈": 2, "로퍼": 4, "힐": 4, "부츠": 3, "샌들": 1, "더비": 5,
    "가방": 3, "액세서리": 3,
}

RAW_GENDER_MAP: dict[str, str] = {
    "여성의류": "female", "남성의류": "male",
    "여성신발": "female", "남성신발": "male",
    "여성가방": "female", "남성가방": "male",
}

MALE_KEYWORDS = {"남성", "남자", "맨즈", "mens", "남성용"}
FEMALE_KEYWORDS = {"여성", "여자", "우먼", "womens", "여성용"}

MAX_ATTEMPTS_PER_OUTFIT = 50
TARGET_OUTFITS_PER_SLOT = 3


def load_recipes() -> tuple[list[dict], dict[str, list[str]]]:
    with open(RECIPES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    season_forbidden = data.get("season_forbidden", {})
    return data["recipes"], season_forbidden


def load_and_classify_items(tone_id: str) -> list[dict]:
    filepath = NORMALIZED_DIR / f"{tone_id}.json"
    if not filepath.exists():
        logger.warning("톤 파일 없음: %s", tone_id)
        return []

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    classified = []
    for item in data["items"]:
        # category가 이미 채워진 경우 (classify_products.py 실행 후)
        if item.get("category"):
            classified.append(item)
            continue

        result = classify_by_keyword(
            item.get("name", ""),
            item.get("raw_category3"),
            item.get("raw_category4"),
        )
        if not result:
            continue

        category = result["category"]
        item["category"] = category
        item["formality"] = DEFAULT_FORMALITY.get(category, 3)

        raw_cat2 = item.get("raw_category2", "")
        item["gender"] = RAW_GENDER_MAP.get(raw_cat2, "unisex")

        if not item.get("age_group"):
            item["age_group"] = "30s"

        classified.append(item)

    return classified


def build_item_pool(
    items: list[dict], gender: str, age_group: str | None = None
) -> dict[str, list[dict]]:
    """성별 + 연령대 필터링 후 카테고리별 아이템 풀을 만든다."""
    opposite_keywords = FEMALE_KEYWORDS if gender == "male" else MALE_KEYWORDS
    pool: dict[str, list[dict]] = {}
    for item in items:
        item_gender = item.get("gender", "unisex")
        if item_gender != gender and item_gender != "unisex":
            continue
        name_lower = item.get("name", "").lower()
        if any(kw in name_lower for kw in opposite_keywords):
            continue
        if age_group:
            item_age = item.get("age_group")
            if item_age and item_age != age_group:
                continue
        cat = item["category"]
        pool.setdefault(cat, []).append(item)
    return pool


def pick_required_items(
    recipe: dict, pool: dict[str, list[dict]]
) -> list[dict] | None:
    if "required_sets" in recipe:
        sets = recipe["required_sets"]
        random.shuffle(sets)
        for req_set in sets:
            items = _pick_from_slots(req_set, pool)
            if items is not None:
                return items
        return None
    else:
        return _pick_from_slots(recipe["required"], pool)


def _pick_from_slots(
    slots: list[list[str]], pool: dict[str, list[dict]]
) -> list[dict] | None:
    selected = []
    for slot in slots:
        candidates = []
        for cat in slot:
            candidates.extend(pool.get(cat, []))
        if not candidates:
            return None
        selected.append(random.choice(candidates))
    return selected


def pick_optional_items(
    recipe: dict, pool: dict[str, list[dict]]
) -> list[dict]:
    optional_items = []
    for opt in recipe.get("optional", []):
        prob = opt.get("probability", 0.5)
        if random.random() > prob:
            continue
        candidates = []
        for cat in opt["categories"]:
            candidates.extend(pool.get(cat, []))
        if candidates:
            optional_items.append(random.choice(candidates))
    return optional_items


def validate_forbidden(items: list[dict], forbidden: list[str]) -> bool:
    for item in items:
        if item["category"] in forbidden:
            return False
    return True


def validate_formality(items: list[dict], formality_range: list[int]) -> bool:
    formalities = [item["formality"] for item in items]
    if max(formalities) - min(formalities) > 2:
        return False
    range_min, range_max = formality_range
    if min(formalities) < range_min - 1 or max(formalities) > range_max + 1:
        return False
    return True


def validate_price_ratio(items: list[dict]) -> bool:
    prices = [item.get("price", 0) for item in items if item.get("price", 0) > 0]
    if len(prices) < 2:
        return True
    return max(prices) / min(prices) <= 3.0


MIN_COLOR_DISTANCE = 25  # RGB 유클리드 거리 최소값


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def validate_color_diversity(items: list[dict]) -> bool:
    """코디 내 색상 다양성 검증. 최대 거리가 40 미만이면 탈락 (전체가 너무 유사)."""
    colors = []
    for item in items:
        hex_color = item.get("color_hex")
        if hex_color and len(hex_color) == 7:
            colors.append(_hex_to_rgb(hex_color))
    if len(colors) < 2:
        return True
    from itertools import combinations
    max_dist = 0.0
    for a, b in combinations(colors, 2):
        dist = ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5
        if dist > max_dist:
            max_dist = dist
    return max_dist >= 40  # 가장 다른 쌍이 최소 40 이상 차이


def make_outfit_id(
    gender: str, tone_id: str, tpo: str, season: str, age_group: str, idx: int
) -> str:
    tone_short = tone_id.replace("_", "")[:8]
    season_short = season[:2]
    age_short = age_group[:2] if age_group else "al"
    return f"outfit_{gender[0]}_{tone_short}_{tpo}_{season_short}_{age_short}_{idx:03d}"


def generate_outfits_for_slot(
    recipe: dict,
    pool: dict[str, list[dict]],
    tone_id: str,
    season: str,
    age_group: str,
    forbidden_extra: list[str],
    seen_combos: set[frozenset[str]],
    target_count: int = TARGET_OUTFITS_PER_SLOT,
) -> list[dict]:
    gender = recipe["gender"]
    tpo = recipe["tpo"]
    moods = recipe["moods"]
    forbidden = list(set(recipe.get("forbidden", []) + forbidden_extra))
    formality_range = recipe.get("formality_range", [1, 5])

    outfits = []
    attempts = 0

    while len(outfits) < target_count and attempts < MAX_ATTEMPTS_PER_OUTFIT * target_count:
        attempts += 1

        required = pick_required_items(recipe, pool)
        if required is None:
            break

        optional = pick_optional_items(recipe, pool)
        items = required + optional

        if not validate_forbidden(items, forbidden):
            continue
        if not validate_color_diversity(items):
            continue
        if not validate_formality(items, formality_range):
            continue
        if not validate_price_ratio(items):
            continue

        item_ids = frozenset(item["product_id"] for item in items)
        if item_ids in seen_combos:
            continue
        seen_combos.add(item_ids)

        has_top_or_onepiece = any(
            item["category"] in (
                "셔츠", "블라우스", "니트", "티셔츠", "맨투맨", "후드",
                "크롭탑", "탱크탑", "폴로", "원피스",
            )
            for item in items
        )
        has_bottom_or_onepiece = any(
            item["category"] in (
                "슬랙스", "청바지", "스커트", "와이드팬츠", "조거팬츠",
                "숏팬츠", "레깅스", "치노", "원피스",
            )
            for item in items
        )
        is_complete = has_top_or_onepiece and has_bottom_or_onepiece

        total_price = sum(item.get("price", 0) for item in items)
        idx = len(outfits) + 1
        outfit_id = make_outfit_id(gender, tone_id, tpo, season, age_group, idx)

        outfit = {
            "id": outfit_id,
            "item_ids": sorted(item["product_id"] for item in items),
            "gender": gender,
            "age_group": age_group,
            "designed_tpo": tpo,
            "designed_moods": moods,
            "designed_season": season,
            "total_price": total_price,
            "lowest_total_price": total_price,
            "is_complete_outfit": is_complete,
            "tags": [tone_id, tpo, gender, season, age_group],
            "scores": None,
            "style_details": None,
            "reasons": None,
            "llm_quality_score": None,
            "items_snapshot": [
                {
                    "product_id": item["product_id"],
                    "name": item["name"],
                    "category": item["category"],
                    "price": item.get("price", 0),
                    "formality": item["formality"],
                    "image_url": item.get("image_url"),
                }
                for item in items
            ],
        }
        outfits.append(outfit)

    return outfits


AGE_GROUPS = ["20s", "30s", "40plus"]


def generate_all(seed: int = 42, target_per_slot: int = TARGET_OUTFITS_PER_SLOT) -> list[dict]:
    random.seed(seed)
    recipes, season_forbidden = load_recipes()
    all_outfits: list[dict] = []
    seen_combos: set[frozenset[str]] = set()

    stats = {
        "by_gender": {"female": 0, "male": 0},
        "by_tpo": {},
        "by_tone": {},
        "by_season": {},
        "by_age": {"20s": 0, "30s": 0, "40plus": 0},
        "incomplete": 0,
        "skipped_slots": 0,
    }

    total_slots = sum(len(r.get("seasons", [])) for r in recipes) * len(TONES_12) * len(AGE_GROUPS)
    logger.info("레시피 %d개, 연령대 %d개, 슬롯 %d개", len(recipes), len(AGE_GROUPS), total_slots)
    logger.info("목표: ~%d개 (target_per_slot=%d)", total_slots * target_per_slot, target_per_slot)

    start = time.time()

    for tone_id in TONES_12:
        logger.info("톤 처리 중: %s", tone_id)
        items = load_and_classify_items(tone_id)
        logger.info("  분류된 아이템: %d개", len(items))

        for recipe in recipes:
            gender = recipe["gender"]
            tpo = recipe["tpo"]
            seasons = recipe.get("seasons", ["spring", "summer", "fall", "winter"])

            for age_group in AGE_GROUPS:
                pool = build_item_pool(items, gender, age_group)

                for season in seasons:
                    forbidden_extra = season_forbidden.get(season, [])

                    outfits = generate_outfits_for_slot(
                        recipe, pool, tone_id, season, age_group, forbidden_extra,
                        seen_combos, target_count=target_per_slot,
                    )

                    if not outfits:
                        stats["skipped_slots"] += 1
                        continue

                    all_outfits.extend(outfits)
                    stats["by_gender"][gender] += len(outfits)
                    stats["by_tpo"][tpo] = stats["by_tpo"].get(tpo, 0) + len(outfits)
                    stats["by_tone"][tone_id] = stats["by_tone"].get(tone_id, 0) + len(outfits)
                    stats["by_season"][season] = stats["by_season"].get(season, 0) + len(outfits)
                    stats["by_age"][age_group] = stats["by_age"].get(age_group, 0) + len(outfits)
                    stats["incomplete"] += sum(1 for o in outfits if not o["is_complete_outfit"])

        logger.info("  톤 완료: %d개 (누적 %d개)",
                    stats["by_tone"].get(tone_id, 0), len(all_outfits))

    elapsed = time.time() - start

    logger.info("=" * 60)
    logger.info("총 생성: %d개 (%.1f초)", len(all_outfits), elapsed)
    logger.info("성별: %s", stats["by_gender"])
    logger.info("연령대: %s", stats["by_age"])
    logger.info("TPO별: %s", stats["by_tpo"])
    logger.info("계절별: %s", stats["by_season"])
    logger.info("미완성 코디: %d개", stats["incomplete"])
    logger.info("건너뛴 슬롯: %d개", stats["skipped_slots"])

    return all_outfits


def main():
    parser = argparse.ArgumentParser(description="레시피 기반 코디 조합 생성 v2")
    parser.add_argument("--seed", type=int, default=42, help="랜덤 시드")
    parser.add_argument("--target", type=int, default=TARGET_OUTFITS_PER_SLOT,
                        help="슬롯당 목표 코디 수 (기본 3)")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH),
                        help="출력 파일 경로")
    parser.add_argument("--dry-run", action="store_true",
                        help="생성만 하고 파일 저장 안 함")
    args = parser.parse_args()

    outfits = generate_all(seed=args.seed, target_per_slot=args.target)

    if not args.dry_run:
        output_path = Path(args.output)
        output_data = {
            "version": "2.0",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_count": len(outfits),
            "outfits": outfits,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info("저장 완료: %s (%d개)", output_path, len(outfits))
    else:
        logger.info("[DRY-RUN] 파일 저장 건너뜀")

    if outfits:
        sample = random.choice(outfits)
        logger.info("샘플 코디: %s", json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
