from contextlib import asynccontextmanager
import logging
import os
import shutil
import sys
import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
import capture_manager
import models  # noqa: F401 — ensures all models are registered with Base.metadata
from database import Base, engine, SessionLocal, get_db
from models.export import ExportJob as ExportJobModel, ExportStatus as ExportStatusEnum
from models.timelapse import Timelapse as TimelapseModel, TimelapseStatus
from routers import cameras, frames, timelapses, settings, exports
from routers.settings import _ensure_settings_row

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Chronicle API starting up...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready!")
    db = SessionLocal()
    try:
        settings = _ensure_settings_row(db)
        storage_path_override = os.getenv("STORAGE_PATH")
        if storage_path_override and settings.storage_path != storage_path_override:
            settings.storage_path = storage_path_override
            db.commit()
        os.makedirs(settings.storage_path, exist_ok=True)
        logger.info("Storage path: %s", settings.storage_path)
        capture_manager.scheduler.configure(timezone=settings.timezone)
        capture_manager.scheduler.start()
        logger.info("Scheduler started (timezone: %s)", settings.timezone)
        # Re-start any timelapses that were running when the server last shut down.
        running = db.query(TimelapseModel).filter(
            TimelapseModel.status == TimelapseStatus.running
        ).all()
        for t in running:
            capture_manager.start(t.id, t.interval_seconds)
        logger.info("Re-started %d running timelapse(s)", len(running))
        # Re-register scheduled-start jobs for pending timelapses with a future start time.
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        pending = db.query(TimelapseModel).filter(
            TimelapseModel.status == TimelapseStatus.pending,
            TimelapseModel.started_at > now_utc,
        ).all()
        for t in pending:
            capture_manager.schedule_start(t.id, t.started_at, t.interval_seconds)
        logger.info("Scheduled %d auto-start job(s)", len(pending))
        # Reset any export jobs that were left in "running" state from a previous session.
        stuck_exports = db.query(ExportJobModel).filter(
            ExportJobModel.status == ExportStatusEnum.running
        ).all()
        for job in stuck_exports:
            job.status = ExportStatusEnum.error
            job.error_message = "Export interrupted by server restart."
        if stuck_exports:
            db.commit()
            logger.warning("Reset %d stuck export job(s) to error", len(stuck_exports))
    finally:
        db.close()
    yield
    logger.info("Chronicle API shutting down...")
    capture_manager.scheduler.shutdown(wait=False)


app = FastAPI(title="Chronicle API", lifespan=lifespan)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
def health(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    scheduler_ok = capture_manager.scheduler.running
    ffmpeg_ok = shutil.which("ffmpeg") is not None

    all_ok = db_ok and scheduler_ok and ffmpeg_ok
    body = {"status": "ok" if all_ok else "degraded", "db": db_ok, "scheduler": scheduler_ok, "ffmpeg": ffmpeg_ok}
    return JSONResponse(content=body, status_code=200 if all_ok else 503)


# Mount the built frontend last so all API and health routes take precedence.
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
