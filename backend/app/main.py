import asyncio
import logging
from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, closet, compare, feed, feedback, item, onboarding, outfit, preference, reaction, saved, subscription, tone, top_pick, tryon, user

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 피드 캐시 백그라운드 프리워밍 (콜드 스타트 지연 제거)
    async def _prewarm_feed_cache():
        try:
            from app.db.session import async_session
            from app.services.feed_service import _load_feed_cache
            async with async_session() as db:
                await _load_feed_cache(db)
            logger.info("Feed cache pre-warmed")
        except Exception as e:
            logger.warning(f"Feed cache pre-warm failed: {e}")

    task = asyncio.create_task(_prewarm_feed_cache())
    app.state.prewarm_task = task
    try:
        yield
    finally:
        if not task.done():
            task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage"
(STORAGE_ROOT / "tryon").mkdir(parents=True, exist_ok=True)
(STORAGE_ROOT / "closet").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STORAGE_ROOT)), name="static")

app.include_router(auth.router)
app.include_router(closet.router)
app.include_router(compare.router)
app.include_router(feed.router)
app.include_router(feedback.router)
app.include_router(item.router)
app.include_router(onboarding.router)
app.include_router(outfit.router)
app.include_router(preference.router)
app.include_router(reaction.router)
app.include_router(saved.router)
app.include_router(subscription.router)
app.include_router(tone.router)
app.include_router(top_pick.router)
app.include_router(tryon.router)
app.include_router(user.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
