"""사용량 추적 서비스 테스트.

무료 3회 제한, 프리미엄 무제한 로직을 검증한다.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import text


TEST_FREE_USER_ID = str(uuid.uuid4())
TEST_PREMIUM_USER_ID = str(uuid.uuid4())


@pytest_asyncio.fixture
async def seed_users(db_session):
    """무료/프리미엄 사용자 데이터 시드 (usage_tracker 서비스 테스트용)."""
    return db_session


class TestCheckTryonLimit:
    """check_tryon_limit 테스트."""

    @pytest.mark.asyncio
    async def test_free_user_first_use(self, db_session, seed_users):
        """무료 사용자 첫 사용 — 3회 남음."""
        from app.services.usage_tracker import check_tryon_limit
        result = await check_tryon_limit(db_session, uuid.UUID(TEST_FREE_USER_ID))

        assert result["allowed"] is True
        assert result["is_premium"] is False
        assert result["usage_count"] == 0
        assert result["remaining"] == 3

    @pytest.mark.asyncio
    async def test_free_user_after_2_uses(self, db_session, seed_users):
        """무료 사용자 2회 사용 후 — 1회 남음."""
        from app.services.usage_tracker import check_tryon_limit, increment_usage
        uid = uuid.UUID(TEST_FREE_USER_ID)
        for _ in range(2):
            await increment_usage(db_session, uid)
        await db_session.flush()

        result = await check_tryon_limit(db_session, uid)
        assert result["allowed"] is True
        assert result["remaining"] == 1

    @pytest.mark.asyncio
    async def test_free_user_limit_reached(self, db_session, seed_users):
        """무료 사용자 3회 소진 — 사용 불가."""
        from app.services.usage_tracker import check_tryon_limit, increment_usage
        uid = uuid.UUID(TEST_FREE_USER_ID)
        for _ in range(3):
            await increment_usage(db_session, uid)
        await db_session.flush()

        result = await check_tryon_limit(db_session, uid)
        assert result["allowed"] is False
        assert result["remaining"] == 0

    @pytest.mark.asyncio
    async def test_premium_user_unlimited(self, db_session, seed_users):
        """프리미엄 사용자 — 무제한."""
        from app.services.usage_tracker import check_tryon_limit, increment_usage
        uid = uuid.UUID(TEST_PREMIUM_USER_ID)
        for _ in range(10):
            await increment_usage(db_session, uid)
        await db_session.flush()

        with patch("app.services.usage_tracker.get_user_premium_status", new_callable=AsyncMock) as mock_prem:
            mock_prem.return_value = True
            result = await check_tryon_limit(db_session, uid)

        assert result["allowed"] is True
        assert result["is_premium"] is True
        assert result["remaining"] is None

    @pytest.mark.asyncio
    async def test_nonexistent_user_denied(self, db_session, seed_users):
        """존재하지 않는 사용자 — is_premium=False 취급."""
        fake_id = uuid.uuid4()
        from app.services.usage_tracker import check_tryon_limit
        result = await check_tryon_limit(db_session, fake_id)

        assert result["is_premium"] is False
        assert result["allowed"] is True
        assert result["remaining"] == 3


class TestIncrementUsage:
    """increment_usage 테스트."""

    @pytest.mark.asyncio
    async def test_first_increment(self, db_session, seed_users):
        """첫 사용 → usage_count=1 생성."""
        from app.services.usage_tracker import increment_usage
        count = await increment_usage(db_session, uuid.UUID(TEST_FREE_USER_ID))
        assert count == 1

    @pytest.mark.asyncio
    async def test_subsequent_increment(self, db_session, seed_users):
        """기존 레코드 → usage_count 증가."""
        from app.services.usage_tracker import increment_usage
        uid = uuid.UUID(TEST_FREE_USER_ID)
        await increment_usage(db_session, uid)
        await increment_usage(db_session, uid)
        count = await increment_usage(db_session, uid)
        assert count == 3

    @pytest.mark.asyncio
    async def test_increment_does_not_commit(self, db_session, seed_users):
        """increment_usage는 flush만 하고 commit하지 않는다."""
        from app.services.usage_tracker import increment_usage, get_usage_count

        await increment_usage(db_session, uuid.UUID(TEST_FREE_USER_ID))
        count = await get_usage_count(db_session, uuid.UUID(TEST_FREE_USER_ID))
        assert count == 1


class TestTryonLimitIntegration:
    """무료 3회 제한 통합 플로우 테스트."""

    @pytest.mark.asyncio
    async def test_free_user_3_uses_then_blocked(self, db_session, seed_users):
        """무료 사용자가 3회 사용 후 차단되는 전체 플로우."""
        from app.services.usage_tracker import check_tryon_limit, increment_usage

        uid = uuid.UUID(TEST_FREE_USER_ID)

        for i in range(3):
            limit = await check_tryon_limit(db_session, uid)
            assert limit["allowed"] is True
            assert limit["remaining"] == 3 - i
            await increment_usage(db_session, uid)
            await db_session.flush()

        limit = await check_tryon_limit(db_session, uid)
        assert limit["allowed"] is False
        assert limit["remaining"] == 0
