from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import closet, compare, feed, item, onboarding, outfit, preference, reaction, tone, top_pick, tryon

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://frontend-nine-nu-tw6mmgf7ut.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(closet.router)
app.include_router(compare.router)
app.include_router(feed.router)
app.include_router(item.router)
app.include_router(onboarding.router)
app.include_router(outfit.router)
app.include_router(preference.router)
app.include_router(reaction.router)
app.include_router(tone.router)
app.include_router(top_pick.router)
app.include_router(tryon.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
