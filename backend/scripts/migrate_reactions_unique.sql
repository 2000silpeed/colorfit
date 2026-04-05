-- 2026-04-05: reactions 테이블에 (user_id, outfit_id, reaction_type) UNIQUE 제약 추가
-- 적용 순서
--   1. 중복 레코드 중 최초(id 최소)만 남기고 제거
--   2. UNIQUE 제약 추가
-- 실행: psql $DATABASE_URL -f scripts/migrate_reactions_unique.sql

BEGIN;

-- 중복 제거 ~ 제약 추가 사이에 신규 중복이 끼어들면 ADD CONSTRAINT가 실패한다.
-- EXCLUSIVE 잠금으로 쓰기 차단 (읽기는 허용).
LOCK TABLE reactions IN EXCLUSIVE MODE;

DELETE FROM reactions
WHERE id IN (
    SELECT id
    FROM (
        SELECT
            id,
            ROW_NUMBER() OVER (
                PARTITION BY user_id, outfit_id, reaction_type
                ORDER BY id ASC
            ) AS rn
        FROM reactions
    ) dedup
    WHERE rn > 1
);

ALTER TABLE reactions
    DROP CONSTRAINT IF EXISTS uq_reactions_user_outfit_type;

ALTER TABLE reactions
    ADD CONSTRAINT uq_reactions_user_outfit_type
    UNIQUE (user_id, outfit_id, reaction_type);

COMMIT;
