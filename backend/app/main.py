from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, closet, compare, feed, feedback, item, onboarding, outfit, preference, reaction, saved, subscription, tone, top_pick, tryon, user


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
