from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime
import os

import capture_manager
import models  # noqa: F401 — ensures all models are registered with Base.metadata
from database import Base, engine, SessionLocal
from models.export import ExportJob as ExportJobModel, ExportStatus as ExportStatusEnum
from models.timelapse import Timelapse as TimelapseModel, TimelapseStatus
from routers import cameras, frames, timelapses, settings, exports
from routers.settings import _ensure_settings_row


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        settings = _ensure_settings_row(db)
        os.makedirs(settings.storage_path, exist_ok=True)
        capture_manager.scheduler.configure(timezone=settings.timezone)
        capture_manager.scheduler.start()
        # Re-start any timelapses that were running when the server last shut down.
        running = db.query(TimelapseModel).filter(
            TimelapseModel.status == TimelapseStatus.running
        ).all()
        for t in running:
            capture_manager.start(t.id, t.interval_seconds)
        # Re-register scheduled-start jobs for pending timelapses with a future start time.
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        pending = db.query(TimelapseModel).filter(
            TimelapseModel.status == TimelapseStatus.pending,
            TimelapseModel.started_at > now_utc,
        ).all()
        for t in pending:
            capture_manager.schedule_start(t.id, t.started_at, t.interval_seconds)
        # Reset any export jobs that were left in "running" state from a previous session.
        stuck_exports = db.query(ExportJobModel).filter(
            ExportJobModel.status == ExportStatusEnum.running
        ).all()
        for job in stuck_exports:
            job.status = ExportStatusEnum.error
            job.error_message = "Export interrupted by server restart."
        if stuck_exports:
            db.commit()
    finally:
        db.close()
    yield
    capture_manager.scheduler.shutdown(wait=False)


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
app.include_router(exports.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
