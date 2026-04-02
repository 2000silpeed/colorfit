"""프리미엄 구독 서비스 테스트."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.services.subscription import subscribe, get_subscription_status, VALID_COUPONS


TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """테스트용 사용자 생성."""
    await db_session.execute(
        text("INSERT INTO users (id, is_premium) VALUES (:id, :premium)"),
        {"id": str(TEST_USER_ID), "premium": False},
    )
    await db_session.commit()
    return db_session


@pytest.mark.asyncio
async def test_subscribe_with_valid_coupon(seeded_db):
    """유효한 쿠폰 코드로 구독 활성화."""
    result = await subscribe(seeded_db, TEST_USER_ID, "monthly", "COLORFIT-BETA")
    await seeded_db.commit()

    assert result["plan"] == "monthly"
    assert result["status"] == "active"
    assert result["price_krw"] == 4900
    assert result["expires_at"] is not None
    assert result["subscription_id"] is not None


@pytest.mark.asyncio
async def test_subscribe_with_yearly_plan(seeded_db):
    """연간 플랜 구독 활성화."""
    result = await subscribe(seeded_db, TEST_USER_ID, "yearly", "PREMIUM-TEST")
    await seeded_db.commit()

    assert result["plan"] == "yearly"
    assert result["price_krw"] == 39000


@pytest.mark.asyncio
async def test_subscribe_invalid_coupon_raises(seeded_db):
    """잘못된 쿠폰 코드 → ValueError."""
    with pytest.raises(ValueError, match="유효하지 않은 쿠폰"):
        await subscribe(seeded_db, TEST_USER_ID, "monthly", "INVALID-CODE")


@pytest.mark.asyncio
async def test_subscribe_no_coupon_raises(seeded_db):
    """쿠폰 코드 없이 구독 시도 → ValueError."""
    with pytest.raises(ValueError, match="유효하지 않은 쿠폰"):
        await subscribe(seeded_db, TEST_USER_ID, "monthly", None)


@pytest.mark.asyncio
async def test_subscribe_invalid_plan_raises(seeded_db):
    """잘못된 플랜 → ValueError."""
    with pytest.raises(ValueError, match="유효하지 않은 플랜"):
        await subscribe(seeded_db, TEST_USER_ID, "weekly", "COLORFIT-BETA")


@pytest.mark.asyncio
async def test_subscribe_duplicate_raises(seeded_db):
    """이미 활성 구독이 있으면 중복 가입 불가."""
    await subscribe(seeded_db, TEST_USER_ID, "monthly", "COLORFIT-BETA")
    await seeded_db.commit()

    with pytest.raises(ValueError, match="이미 활성 구독"):
        await subscribe(seeded_db, TEST_USER_ID, "yearly", "PREMIUM-TEST")


@pytest.mark.asyncio
async def test_subscribe_updates_user_premium_flag(seeded_db):
    """구독 시 users.is_premium이 True로 업데이트."""
    await subscribe(seeded_db, TEST_USER_ID, "monthly", "COLORFIT-BETA")
    await seeded_db.commit()

    result = await seeded_db.execute(
        text("SELECT is_premium FROM users WHERE id = :id"),
        {"id": str(TEST_USER_ID)},
    )
    row = result.fetchone()
    assert bool(row[0]) is True


@pytest.mark.asyncio
async def test_get_status_no_subscription(seeded_db):
    """구독 없는 사용자 → is_premium: False."""
    result = await get_subscription_status(seeded_db, TEST_USER_ID)
    assert result["is_premium"] is False
    assert result["plan"] is None


@pytest.mark.asyncio
async def test_get_status_with_subscription(seeded_db):
    """활성 구독이 있으면 상태 반환."""
    await subscribe(seeded_db, TEST_USER_ID, "yearly", "COLORFIT-BETA")
    await seeded_db.commit()

    result = await get_subscription_status(seeded_db, TEST_USER_ID)
    assert result["is_premium"] is True
    assert result["plan"] == "yearly"
    assert result["status"] == "active"


@pytest.mark.asyncio
async def test_coupon_case_insensitive(seeded_db):
    """쿠폰 코드 대소문자 무관."""
    result = await subscribe(seeded_db, TEST_USER_ID, "monthly", "colorfit-beta")
    assert result["status"] == "active"
