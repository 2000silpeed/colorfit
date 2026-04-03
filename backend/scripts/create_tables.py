"""Supabase DB에 ORM 모델 기반 테이블 생성 (asyncpg 직접 사용)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg

from app.config import settings


DDL = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255),
    provider VARCHAR(20),
    gender VARCHAR(10),
    tone_id VARCHAR(30),
    tpo_primary VARCHAR(20),
    tpo_secondary VARCHAR(20),
    tpo_list TEXT[],
    style_moods TEXT[],
    budget_min INTEGER,
    budget_max INTEGER,
    is_premium BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_gender ON users(gender);
CREATE INDEX IF NOT EXISTS ix_users_tone_id ON users(tone_id);

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(500),
    brand VARCHAR(100),
    category VARCHAR(20),
    color_hex VARCHAR(7),
    tone_id VARCHAR(30),
    price INTEGER,
    mall_name VARCHAR(50),
    mall_url TEXT,
    image_url TEXT,
    tags TEXT[],
    gender VARCHAR(10),
    silhouette VARCHAR(20),
    formality SMALLINT,
    last_observed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_products_tone_id ON products(tone_id);
CREATE INDEX IF NOT EXISTS ix_products_gender ON products(gender);

CREATE TABLE IF NOT EXISTS outfits (
    id VARCHAR(50) PRIMARY KEY,
    item_ids TEXT[],
    gender VARCHAR(10),
    designed_tpo VARCHAR(20),
    designed_season VARCHAR(10),
    designed_moods TEXT[],
    total_price INTEGER,
    lowest_total_price INTEGER,
    is_complete_outfit BOOLEAN,
    tags TEXT[],
    scores JSONB,
    style_details JSONB,
    reasons TEXT[],
    llm_quality_score SMALLINT
);
CREATE INDEX IF NOT EXISTS ix_outfits_designed_tpo ON outfits(designed_tpo);
CREATE INDEX IF NOT EXISTS ix_outfits_gender ON outfits(gender);

CREATE TABLE IF NOT EXISTS reactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36),
    outfit_id VARCHAR(50),
    reaction_type VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS style_seeds (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mood_seed VARCHAR(30),
    silhouette_seed VARCHAR(30),
    color_seed VARCHAR(30),
    price_seed VARCHAR(30),
    seed_confidence INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tone_preferences JSONB DEFAULT '{}'::jsonb,
    category_preferences JSONB DEFAULT '{}'::jsonb,
    brand_preferences JSONB DEFAULT '{}'::jsonb,
    avg_liked_price INTEGER,
    feedback_count INTEGER DEFAULT 0,
    weight_overrides JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS closet_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    image_url VARCHAR(2048) NOT NULL,
    category VARCHAR(50),
    dominant_color_hex VARCHAR(7),
    matched_tone_id VARCHAR(30),
    pcf_score FLOAT,
    overall_score FLOAT,
    reasons TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_closet_items_user_id ON closet_items(user_id);

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    plan VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    coupon_code VARCHAR(50),
    price_krw INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions(user_id);
"""


async def main():
    url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    print(f"DB: {url[:60]}...")

    conn = await asyncpg.connect(url, statement_cache_size=0)
    try:
        await conn.execute(DDL)
        print("✅ 8개 테이블 + 인덱스 생성 완료")

        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        print(f"현재 테이블: {[t['tablename'] for t in tables]}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
