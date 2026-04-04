"""피드백 개인화 학습 테스트 — Task 4.10.

preference_tracker 서비스 + POST /api/feedback 라우터 검증.
"""

import json
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.preference_tracker import (
    ACTION_WEIGHTS,
    _compute_weight_overrides,
    _learning_phase,
    _update_preference_dict,
    compute_personalization_bonus,
    record_feedback,
    DEFAULT_WEIGHTS,
    WEIGHT_OVERRIDE_THRESHOLD,
)


# ---------------------------------------------------------------------------
# 1. 순수 함수 단위 테스트
# ---------------------------------------------------------------------------


class TestActionWeights:
    def test_weights_defined(self):
        assert ACTION_WEIGHTS["save"] == 2.0
        assert ACTION_WEIGHTS["like"] == 1.0
        assert ACTION_WEIGHTS["click"] == 0.3
        assert ACTION_WEIGHTS["dislike"] == -1.5

    def test_positive_vs_negative_balance(self):
        """부정 신호 절대값이 save보다 작아야 한다 (다양성 보호)."""
        assert abs(ACTION_WEIGHTS["dislike"]) < ACTION_WEIGHTS["save"]


class TestLearningPhase:
    def test_seed_phase(self):
        assert _learning_phase(0) == "seed"

    def test_hybrid_phase(self):
        assert _learning_phase(1) == "hybrid"
        assert _learning_phase(15) == "hybrid"
        assert _learning_phase(29) == "hybrid"

    def test_learned_phase(self):
        assert _learning_phase(30) == "learned"
        assert _learning_phase(100) == "learned"


class TestUpdatePreferenceDict:
    def test_add_new_key(self):
        result = _update_preference_dict({}, "spring_warm_light", 2.0)
        assert result["spring_warm_light"] == 2.0

    def test_accumulate_existing(self):
        current = {"top": 3.0}
        result = _update_preference_dict(current, "top", 1.0)
        assert result["top"] == 4.0

    def test_none_key_ignored(self):
        current = {"a": 1.0}
        result = _update_preference_dict(current, None, 2.0)
        assert result == {"a": 1.0}

    def test_negative_weight(self):
        current = {"top": 2.0}
        result = _update_preference_dict(current, "top", -1.5)
        assert result["top"] == pytest.approx(0.5)


class TestComputeWeightOverrides:
    def test_default_when_no_concentration(self):
        """선호 집중 없을 때 기본 가중치 비율 유지."""
        tone = {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0, "e": 1.0}
        cat = {"x": 1.0, "y": 1.0, "z": 1.0, "w": 1.0}
        result = _compute_weight_overrides(tone, cat, None, 3)
        total = sum(result.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_tone_concentration_boosts_pcf(self):
        """톤 집중 80%+ → PCF 가중치 상승."""
        tone = {"spring_warm_light": 10.0, "spring_warm_bright": 1.0}
        cat = {"x": 1.0, "y": 1.0, "z": 1.0, "w": 1.0}
        result = _compute_weight_overrides(tone, cat, None, 3)
        assert result["pcf"] > DEFAULT_WEIGHTS["pcf"]

    def test_category_concentration_boosts_sf(self):
        """카테고리 상위 3개가 80%+ → SF 가중치 상승."""
        tone = {"a": 1.0, "b": 1.0, "c": 1.0}
        cat = {"블라우스": 10.0, "슬랙스": 5.0, "로퍼": 3.0}
        result = _compute_weight_overrides(tone, cat, None, 3)
        assert result["sf"] > DEFAULT_WEIGHTS["sf"]

    def test_price_sensitivity_boosts_pe(self):
        """가격 선호 패턴 (5건+) → PE 가중치 상승."""
        tone = {"a": 1.0}
        cat = {"x": 1.0}
        result = _compute_weight_overrides(tone, cat, 50000, 5)
        assert result["pe"] > DEFAULT_WEIGHTS["pe"]

    def test_normalized_to_one(self):
        """모든 케이스에서 합이 1.0."""
        tone = {"spring_warm_light": 10.0}
        cat = {"블라우스": 10.0}
        result = _compute_weight_overrides(tone, cat, 50000, 5)
        assert sum(result.values()) == pytest.approx(1.0, abs=0.01)


class TestPersonalizationBonus:
    def test_positive_bonus(self):
        items = [
            {"tone_id": "spring_warm_light", "category": "블라우스", "brand": "ZARA"},
        ]
        tone_prefs = {"spring_warm_light": 5.0}
        cat_prefs = {"블라우스": 3.0}
        brand_prefs = {"ZARA": 2.0}
        bonus = compute_personalization_bonus({}, items, tone_prefs, cat_prefs, brand_prefs)
        assert bonus > 0

    def test_negative_bonus(self):
        items = [
            {"tone_id": "winter_cool_deep", "category": "패딩", "brand": "X"},
        ]
        tone_prefs = {"winter_cool_deep": -5.0}
        cat_prefs = {"패딩": -3.0}
        brand_prefs = {"X": -2.0}
        bonus = compute_personalization_bonus({}, items, tone_prefs, cat_prefs, brand_prefs)
        assert bonus < 0

    def test_clamped_range(self):
        """보정 점수는 -10 ~ +10 범위."""
        items = [{"tone_id": f"t{i}", "category": f"c{i}", "brand": f"b{i}"} for i in range(20)]
        prefs = {f"t{i}": 100.0 for i in range(20)}
        cat_prefs = {f"c{i}": 100.0 for i in range(20)}
        brand_prefs = {f"b{i}": 100.0 for i in range(20)}
        bonus = compute_personalization_bonus({}, items, prefs, cat_prefs, brand_prefs)
        assert -10.0 <= bonus <= 10.0

    def test_no_matching_prefs(self):
        items = [{"tone_id": "unknown", "category": "unknown", "brand": "unknown"}]
        bonus = compute_personalization_bonus({}, items, {}, {}, {})
        assert bonus == 0.0


# ---------------------------------------------------------------------------
# 2. DB 통합 테스트 (record_feedback)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession):
    """테스트용 outfit + products + user 시드 데이터."""
    user_id = str(uuid.uuid4())

    await db_session.execute(
        text("INSERT INTO users (id, gender, tone_id) VALUES (:id, :g, :t)"),
        {"id": user_id, "g": "female", "t": "spring_warm_light"},
    )

    outfit_id = "outfit-test-001"
    item_ids = json.dumps(["prod-001", "prod-002"])
    await db_session.execute(
        text(
            "INSERT INTO outfits (id, item_ids, total_price) VALUES (:id, :items, :price)"
        ),
        {"id": outfit_id, "items": item_ids, "price": 89000},
    )

    await db_session.execute(
        text(
            "INSERT INTO products (id, tone_id, category, brand, price) "
            "VALUES (:id, :tone, :cat, :brand, :price)"
        ),
        {"id": "prod-001", "tone": "spring_warm_light", "cat": "블라우스", "brand": "ZARA", "price": 49000},
    )
    await db_session.execute(
        text(
            "INSERT INTO products (id, tone_id, category, brand, price) "
            "VALUES (:id, :tone, :cat, :brand, :price)"
        ),
        {"id": "prod-002", "tone": "spring_warm_bright", "cat": "슬랙스", "brand": "H&M", "price": 40000},
    )

    await db_session.commit()
    return user_id, outfit_id


@pytest.mark.asyncio
async def test_record_feedback_creates_preference(db_session, seeded_db):
    """첫 피드백 시 user_preferences 행이 생성되고 선호도가 누적된다."""
    user_id, outfit_id = seeded_db
    count, phase = await record_feedback(db_session, user_id, outfit_id, "save")

    assert count == 1
    assert phase == "hybrid"

    row = (
        await db_session.execute(
            text("SELECT * FROM user_preferences WHERE user_id = :uid"),
            {"uid": user_id},
        )
    ).mappings().first()

    assert row is not None
    assert row["feedback_count"] == 1

    tone_prefs = json.loads(row["tone_preferences"]) if isinstance(row["tone_preferences"], str) else row["tone_preferences"]
    assert tone_prefs.get("spring_warm_light") == 2.0
    assert tone_prefs.get("spring_warm_bright") == 2.0


@pytest.mark.asyncio
async def test_record_feedback_accumulates(db_session, seeded_db):
    """여러 피드백이 누적되어 선호도가 합산된다."""
    user_id, outfit_id = seeded_db

    await record_feedback(db_session, user_id, outfit_id, "save")
    await record_feedback(db_session, user_id, outfit_id, "like")

    row = (
        await db_session.execute(
            text("SELECT * FROM user_preferences WHERE user_id = :uid"),
            {"uid": user_id},
        )
    ).mappings().first()

    assert row["feedback_count"] == 2
    tone_prefs = json.loads(row["tone_preferences"]) if isinstance(row["tone_preferences"], str) else row["tone_preferences"]
    # save(+2.0) + like(+1.0) = 3.0
    assert tone_prefs.get("spring_warm_light") == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_dislike_reduces_preference(db_session, seeded_db):
    """dislike는 선호도를 감소시킨다."""
    user_id, outfit_id = seeded_db

    await record_feedback(db_session, user_id, outfit_id, "save")
    await record_feedback(db_session, user_id, outfit_id, "dislike")

    row = (
        await db_session.execute(
            text("SELECT * FROM user_preferences WHERE user_id = :uid"),
            {"uid": user_id},
        )
    ).mappings().first()

    tone_prefs = json.loads(row["tone_preferences"]) if isinstance(row["tone_preferences"], str) else row["tone_preferences"]
    # save(+2.0) + dislike(-1.5) = 0.5
    assert tone_prefs.get("spring_warm_light") == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_weight_overrides_generated_at_threshold(db_session, seeded_db):
    """10건 이상 축적 시 weight_overrides가 자동 생성된다."""
    user_id, outfit_id = seeded_db

    for _ in range(WEIGHT_OVERRIDE_THRESHOLD):
        await record_feedback(db_session, user_id, outfit_id, "save")

    row = (
        await db_session.execute(
            text("SELECT weight_overrides FROM user_preferences WHERE user_id = :uid"),
            {"uid": user_id},
        )
    ).mappings().first()

    overrides = json.loads(row["weight_overrides"]) if isinstance(row["weight_overrides"], str) else row["weight_overrides"]
    assert overrides is not None
    assert "pcf" in overrides
    assert "of" in overrides
    assert "sf" in overrides
    assert sum(overrides.values()) == pytest.approx(1.0, abs=0.01)


@pytest.mark.asyncio
async def test_nonexistent_outfit_returns_seed(db_session, seeded_db):
    """존재하지 않는 outfit_id에 대해 (0, 'seed')를 반환한다."""
    user_id, _ = seeded_db
    count, phase = await record_feedback(db_session, user_id, "nonexistent", "click")
    assert count == 0
    assert phase == "seed"


@pytest.mark.asyncio
async def test_avg_liked_price_updated_on_positive(db_session, seeded_db):
    """긍정 피드백 시 avg_liked_price가 업데이트된다."""
    user_id, outfit_id = seeded_db

    await record_feedback(db_session, user_id, outfit_id, "save")

    row = (
        await db_session.execute(
            text("SELECT avg_liked_price FROM user_preferences WHERE user_id = :uid"),
            {"uid": user_id},
        )
    ).mappings().first()

    assert row["avg_liked_price"] == 89000


# ---------------------------------------------------------------------------
# 3. API 엔드포인트 테스트
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def api_client(db_session, seeded_db):
    """FastAPI 테스트 클라이언트."""
    from app.main import app
    from app.db.session import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, seeded_db

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_feedback_endpoint(api_client):
    """POST /api/feedback가 올바른 응답을 반환한다."""
    client, (user_id, outfit_id) = api_client
    resp = await client.post("/api/feedback", json={
        "user_id": user_id,
        "outfit_id": outfit_id,
        "action": "save",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["feedback_count"] == 1
    assert data["learning_phase"] == "hybrid"


@pytest.mark.asyncio
async def test_post_feedback_invalid_action(api_client):
    """유효하지 않은 action은 422를 반환한다."""
    client, (user_id, outfit_id) = api_client
    resp = await client.post("/api/feedback", json={
        "user_id": user_id,
        "outfit_id": outfit_id,
        "action": "invalid",
    })
    assert resp.status_code == 422
