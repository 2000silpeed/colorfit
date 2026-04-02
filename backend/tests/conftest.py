"""테스트 공통 픽스처.

PostgreSQL 전용 타입(ARRAY, JSONB)을 SQLite 호환 타입으로 매핑.
필요한 테이블만 생성하여 server_default 호환성 문제를 회피.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest_asyncio
from sqlalchemy import ARRAY as SA_ARRAY, Table, Column, String, Float, Integer, SmallInteger, Boolean, Text, JSON
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

users_table = Table(
    "users", test_metadata,
    Column("id", String(36), primary_key=True),
    Column("email", String(255)),
    Column("provider", String(20)),
    Column("gender", String(10)),
    Column("tone_id", String(30)),
    Column("tpo_primary", String(20)),
    Column("tpo_secondary", String(20)),
    Column("tpo_list", Text),       # ARRAY → TEXT
    Column("style_moods", Text),    # ARRAY → TEXT
    Column("budget_min", Integer),
    Column("budget_max", Integer),
    Column("is_premium", Boolean, default=False),
    Column("created_at", Text),
)

tryon_usage_table = Table(
    "tryon_usage", test_metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(36), unique=True, index=True, nullable=False),
    Column("usage_count", Integer, default=0),
    Column("created_at", Text),
    Column("updated_at", Text),
)

style_seeds_table = Table(
    "style_seeds", test_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(36)),
    Column("mood_seed", String(30)),
    Column("silhouette_seed", String(30)),
    Column("color_seed", String(30)),
    Column("price_seed", String(30)),
    Column("seed_confidence", Integer),
    Column("created_at", Text),
)


tryon_cache_table = Table(
    "tryon_cache", test_metadata,
    Column("id", String(36), primary_key=True),
    Column("outfit_id", String(50), index=True, nullable=False),
    Column("closet_item_id", String(36), nullable=True),
    Column("user_id", String(36), index=True, nullable=False),
    Column("image_url", Text, nullable=False),
    Column("created_at", Text),
)

subscriptions_table = Table(
    "subscriptions", test_metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(36), index=True, nullable=False),
    Column("plan", String(20), nullable=False),
    Column("status", String(20), nullable=False, default="active"),
    Column("coupon_code", String(50)),
    Column("price_krw", Integer, nullable=False),
    Column("created_at", Text),
    Column("expires_at", Text),
)

closet_items_table = Table(
    "closet_items", test_metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(36), index=True, nullable=False),
    Column("image_url", String(2048), nullable=False),
    Column("category", String(50)),
    Column("dominant_color_hex", String(7)),
    Column("matched_tone_id", String(30)),
    Column("pcf_score", Float),
    Column("overall_score", Float),
    Column("reasons", Text),        # ARRAY → TEXT
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
