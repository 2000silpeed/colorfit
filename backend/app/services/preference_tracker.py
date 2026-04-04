"""피드백 개인화 학습 — PreferenceTracker.

기획서 섹션 6.8 구현.
사용자 피드백을 수집하여 tone/category/brand/price 선호도를 누적하고,
10건+ 축적 시 weight_overrides를 자동 생성한다.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ACTION_WEIGHTS: dict[str, float] = {
    "save": 2.0,
    "like": 1.0,
    "click": 0.3,
    "dislike": -1.5,
}

WEIGHT_OVERRIDE_THRESHOLD = 10

DEFAULT_WEIGHTS: dict[str, float] = {
    "pcf": 0.25,
    "of": 0.20,
    "ch": 0.15,
    "pe": 0.15,
    "sf": 0.25,
}


async def _fetch_outfit_items(
    db: AsyncSession, outfit_id: str
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """코디와 아이템 정보를 조회한다."""
    outfit_row = (
        await db.execute(
            text(
                "SELECT id, item_ids, total_price FROM outfits WHERE id = :oid"
            ),
            {"oid": outfit_id},
        )
    ).mappings().first()

    if not outfit_row:
        return None, []

    raw_ids = outfit_row["item_ids"]
    if not raw_ids:
        return dict(outfit_row), []

    # item_ids가 JSON 문자열인 경우 (SQLite) 또는 리스트인 경우 (PostgreSQL)
    if isinstance(raw_ids, str):
        item_ids = json.loads(raw_ids)
    else:
        item_ids = list(raw_ids)

    if not item_ids:
        return dict(outfit_row), []

    # IN 절로 조회 (SQLite/PostgreSQL 모두 호환)
    placeholders = ", ".join(f":id_{i}" for i in range(len(item_ids)))
    params = {f"id_{i}": pid for i, pid in enumerate(item_ids)}
    items_result = await db.execute(
        text(
            f"SELECT id, tone_id, category, brand, price "
            f"FROM products WHERE id IN ({placeholders})"
        ),
        params,
    )
    items = [dict(row) for row in items_result.mappings().all()]
    return dict(outfit_row), items


def _update_preference_dict(
    current: dict[str, float], key: str | None, weight: float
) -> dict[str, float]:
    """선호도 딕셔너리에 가중치를 누적한다."""
    if not key:
        return current
    current[key] = current.get(key, 0.0) + weight
    return current


def _compute_weight_overrides(
    tone_prefs: dict[str, float],
    category_prefs: dict[str, float],
    avg_liked_price: int | None,
    positive_count: int,
) -> dict[str, float]:
    """선호 집중도를 분석하여 가중치 조정값을 생성한다.

    기획서 섹션 6.8 가중치 조정 로직:
    - 톤 선호 집중 (긍정 80%+가 2개 이하 톤) → PCF +0.05
    - 카테고리 선호 뚜렷 (상위 3개가 80%+) → SF +0.05
    - 가격 선호 패턴 (5건+ 저장의 가격 편차 < 20%) → PE +0.03
    - 전체 합 = 1.0 정규화
    """
    overrides = dict(DEFAULT_WEIGHTS)

    # 톤 집중도
    positive_tones = {k: v for k, v in tone_prefs.items() if v > 0}
    if positive_tones:
        total_positive = sum(positive_tones.values())
        sorted_tones = sorted(positive_tones.values(), reverse=True)
        top2_sum = sum(sorted_tones[:2])
        if total_positive > 0 and top2_sum / total_positive >= 0.8:
            overrides["pcf"] += 0.05

    # 카테고리 집중도
    positive_cats = {k: v for k, v in category_prefs.items() if v > 0}
    if positive_cats:
        total_positive = sum(positive_cats.values())
        sorted_cats = sorted(positive_cats.values(), reverse=True)
        top3_sum = sum(sorted_cats[:3])
        if total_positive > 0 and top3_sum / total_positive >= 0.8:
            overrides["sf"] += 0.05

    # 가격 민감도 (avg_liked_price가 있고 5건 이상)
    if avg_liked_price and positive_count >= 5:
        overrides["pe"] += 0.03

    # 정규화: 합 = 1.0
    total = sum(overrides.values())
    if total > 0:
        overrides = {k: round(v / total, 4) for k, v in overrides.items()}

    return overrides


def compute_personalization_bonus(
    outfit_data: dict[str, Any],
    items: list[dict[str, Any]],
    tone_prefs: dict[str, float],
    category_prefs: dict[str, float],
    brand_prefs: dict[str, float],
) -> float:
    """개인화 보정 점수 (-10 ~ +10)를 계산한다.

    사용자의 선호 톤/카테고리/브랜드 일치 여부에 따라 보정한다.
    """
    bonus = 0.0

    for item in items:
        tone_id = item.get("tone_id")
        if tone_id and tone_id in tone_prefs:
            score = tone_prefs[tone_id]
            bonus += min(2.0, max(-2.0, score * 0.3))

        category = item.get("category")
        if category and category in category_prefs:
            score = category_prefs[category]
            bonus += min(2.0, max(-2.0, score * 0.3))

        brand = item.get("brand")
        if brand and brand in brand_prefs:
            score = brand_prefs[brand]
            bonus += min(1.0, max(-1.0, score * 0.2))

    return round(max(-10.0, min(10.0, bonus)), 2)


async def record_feedback(
    db: AsyncSession,
    user_id: str,
    outfit_id: str,
    action: str,
) -> tuple[int, str]:
    """피드백을 기록하고 선호도를 누적 업데이트한다.

    Returns:
        (feedback_count, learning_phase)
    """
    weight = ACTION_WEIGHTS.get(action, 0.0)

    outfit, items = await _fetch_outfit_items(db, outfit_id)
    if not outfit:
        logger.warning("outfit not found: %s", outfit_id)
        return 0, "seed"

    # 현재 user_preferences 조회 (없으면 생성)
    pref_row = (
        await db.execute(
            text(
                "SELECT id, tone_preferences, category_preferences, "
                "brand_preferences, avg_liked_price, feedback_count "
                "FROM user_preferences WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
    ).mappings().first()

    if not pref_row:
        await db.execute(
            text(
                "INSERT INTO user_preferences (user_id, feedback_count) "
                "VALUES (:uid, 0)"
            ),
            {"uid": user_id},
        )
        await db.flush()
        pref_row = (
            await db.execute(
                text(
                    "SELECT id, tone_preferences, category_preferences, "
                    "brand_preferences, avg_liked_price, feedback_count "
                    "FROM user_preferences WHERE user_id = :uid"
                ),
                {"uid": user_id},
            )
        ).mappings().first()

    tone_prefs: dict[str, float] = _parse_json_field(pref_row["tone_preferences"])
    cat_prefs: dict[str, float] = _parse_json_field(pref_row["category_preferences"])
    brand_prefs: dict[str, float] = _parse_json_field(pref_row["brand_preferences"])
    avg_price: int | None = pref_row["avg_liked_price"]
    count: int = (pref_row["feedback_count"] or 0) + 1

    # 아이템별 선호도 누적
    for item in items:
        tone_prefs = _update_preference_dict(tone_prefs, item.get("tone_id"), weight)
        cat_prefs = _update_preference_dict(cat_prefs, item.get("category"), weight)
        brand_prefs = _update_preference_dict(brand_prefs, item.get("brand"), weight)

    # 긍정 액션일 때 가격 선호 업데이트
    if weight > 0 and outfit.get("total_price"):
        outfit_price = outfit["total_price"]
        if avg_price:
            avg_price = round((avg_price + outfit_price) / 2)
        else:
            avg_price = outfit_price

    # weight_overrides 자동 생성 (10건+)
    # positive_count = 긍정 피드백(save/like/click) 건수
    positive_actions = {"save", "like", "click"}
    positive_feedback_count = count if action in positive_actions else max(0, count - 1)
    weight_overrides = None
    if count >= WEIGHT_OVERRIDE_THRESHOLD:
        weight_overrides = _compute_weight_overrides(
            tone_prefs, cat_prefs, avg_price, positive_feedback_count
        )

    # DB 엔진 감지 (SQLite vs PostgreSQL)
    dialect = db.bind.dialect.name if db.bind else "postgresql"
    if dialect == "sqlite":
        sql = (
            "UPDATE user_preferences SET "
            "tone_preferences = :tp, "
            "category_preferences = :cp, "
            "brand_preferences = :bp, "
            "avg_liked_price = :ap, "
            "feedback_count = :fc, "
            "weight_overrides = :wo, "
            "updated_at = CURRENT_TIMESTAMP "
            "WHERE user_id = :uid"
        )
    else:
        sql = (
            "UPDATE user_preferences SET "
            "tone_preferences = :tp::jsonb, "
            "category_preferences = :cp::jsonb, "
            "brand_preferences = :bp::jsonb, "
            "avg_liked_price = :ap, "
            "feedback_count = :fc, "
            "weight_overrides = :wo::jsonb, "
            "updated_at = NOW() "
            "WHERE user_id = :uid"
        )

    await db.execute(
        text(sql),
        {
            "tp": _json_str(tone_prefs),
            "cp": _json_str(cat_prefs),
            "bp": _json_str(brand_prefs),
            "ap": avg_price,
            "fc": count,
            "wo": _json_str(weight_overrides) if weight_overrides else None,
            "uid": user_id,
        },
    )
    await db.commit()

    phase = _learning_phase(count)
    return count, phase


def _learning_phase(feedback_count: int) -> str:
    if feedback_count == 0:
        return "seed"
    elif feedback_count < 30:
        return "hybrid"
    return "learned"


def _parse_json_field(value: Any) -> dict[str, float]:
    """DB에서 읽은 JSON 필드를 딕셔너리로 변환한다."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _json_str(data: dict | None) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)
