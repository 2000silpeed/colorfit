"""테스트 공통 픽스처.

PostgreSQL 전용 타입(ARRAY, JSONB)을 SQLite 호환 타입으로 매핑.
필요한 테이블만 생성하여 server_default 호환성 문제를 회피.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest_asyncio
from sqlalchemy import ARRAY as SA_ARRAY, Table, Column, String, Integer, SmallInteger, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy import MetaData

from app.db.base import Base


@compiles(SA_ARRAY, "sqlite")
def _compile_sa_array(type_, compiler, **kw):
    return "TEXT"


@compiles(PG_ARRAY, "sqlite")
def _compile_pg_array(type_, compiler, **kw):
    return "TEXT"


@compiles(JSONB, "sqlite")
def _compile_jsonb(type_, compiler, **kw):
    return "JSON"


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# SQLite 호환 테스트용 테이블 정의
test_metadata = MetaData()

outfits_table = Table(
    "outfits", test_metadata,
    Column("id", String(50), primary_key=True),
    Column("item_ids", Text),          # ARRAY → TEXT (JSON 문자열)
    Column("gender", String(10)),
    Column("designed_tpo", String(20)),
    Column("designed_season", String(10)),
    Column("designed_moods", Text),     # ARRAY → TEXT
    Column("total_price", Integer),
    Column("lowest_total_price", Integer),
    Column("is_complete_outfit", Boolean),
    Column("tags", Text),              # ARRAY → TEXT
    Column("scores", JSON),            # JSONB → JSON
    Column("style_details", JSON),
    Column("reasons", Text),           # ARRAY → TEXT
    Column("llm_quality_score", SmallInteger),
)

products_table = Table(
    "products", test_metadata,
    Column("id", String(50), primary_key=True),
    Column("name", String(500)),
    Column("brand", String(100)),
    Column("category", String(20)),
    Column("color_hex", String(7)),
    Column("tone_id", String(30)),
    Column("price", Integer),
    Column("mall_name", String(50)),
    Column("mall_url", Text),
    Column("image_url", Text),
    Column("tags", Text),
    Column("gender", String(10)),
    Column("silhouette", String(20)),
    Column("formality", SmallInteger),
    Column("last_observed_at", Text),
)

reactions_table = Table(
    "reactions", test_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(36)),
    Column("outfit_id", String(50)),
    Column("reaction_type", String(10)),
    Column("created_at", Text),
)


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(test_metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(test_metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
