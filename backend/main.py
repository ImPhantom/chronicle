from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401 — ensures all models are registered with Base.metadata
from database import Base, engine, SessionLocal
from routers import cameras, frames, timelapses, settings
from routers.settings import _ensure_settings_row


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _ensure_settings_row(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Chronicle API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router, prefix="/api/v1")
app.include_router(timelapses.router, prefix="/api/v1")
app.include_router(frames.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
