import asyncio
import datetime
import logging
import os
import shutil

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from capture import CaptureError, _FORMAT_EXT, capture_hardware_bytes, capture_network_bytes
from database import SessionLocal
from models.camera import ConnectionType
from models.frame import Frame
from models.settings import AppSettings
from models.timelapse import Timelapse, TimelapseStatus

logger = logging.getLogger(__name__)

# Timezone is configured at startup from AppSettings before scheduler.start() is called.
scheduler = AsyncIOScheduler()


def start(timelapse_id: int, interval_seconds: int) -> None:
    logger.info("Starting capture for timelapse %d every %ds", timelapse_id, interval_seconds)
    # Cancel any pending scheduled-start job before launching the capture loop.
    try:
        scheduler.remove_job(f"timelapse_start_{timelapse_id}")
    except Exception:
        pass
    scheduler.add_job(
        _capture_job,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id=f"timelapse_{timelapse_id}",
        args=[timelapse_id],
        replace_existing=True,
        next_run_time=datetime.datetime.now(datetime.timezone.utc),
    )


def schedule_start(timelapse_id: int, start_at: datetime.datetime, interval_seconds: int) -> None:
    """Register a one-shot job that auto-starts capture at start_at (UTC)."""
    logger.info("Scheduling auto-start for timelapse %d at %s", timelapse_id, start_at)
    scheduler.add_job(
        _auto_start_job,
        trigger=DateTrigger(run_date=start_at),
        id=f"timelapse_start_{timelapse_id}",
        args=[timelapse_id, interval_seconds],
        replace_existing=True,
    )


def pause(timelapse_id: int) -> None:
    logger.info("Pausing capture for timelapse %d", timelapse_id)
    try:
        scheduler.pause_job(f"timelapse_{timelapse_id}")
    except Exception:  # job may not exist if server restarted in paused state
        pass


def resume(timelapse_id: int) -> None:
    logger.info("Resuming capture for timelapse %d", timelapse_id)
    try:
        scheduler.resume_job(f"timelapse_{timelapse_id}")
    except Exception:
        # Job doesn't exist (e.g. server restarted while paused) — re-create it.
        db = SessionLocal()
        try:
            timelapse = db.get(Timelapse, timelapse_id)
            if timelapse is not None:
                start(timelapse_id, timelapse.interval_seconds)
        finally:
            db.close()


def stop(timelapse_id: int) -> None:
    """Cancel both the capture loop and any pending scheduled-start job."""
    logger.info("Stopping capture jobs for timelapse %d", timelapse_id)
    for job_id in [f"timelapse_{timelapse_id}", f"timelapse_start_{timelapse_id}"]:
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass


async def _auto_start_job(timelapse_id: int, interval_seconds: int) -> None:
    """One-shot job: transitions a pending timelapse to running at its scheduled start time."""
    db = SessionLocal()
    try:
        timelapse = db.get(Timelapse, timelapse_id)
        if timelapse is None or timelapse.status != TimelapseStatus.pending:
            return
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        # Edge case: ended_at already passed by the time the start job fires.
        if timelapse.ended_at and now_utc >= timelapse.ended_at:
            logger.warning(
                "Timelapse %d scheduled start fired but end time already passed — completing",
                timelapse_id,
            )
            timelapse.status = TimelapseStatus.completed
            db.commit()
            return
        logger.info("Auto-starting timelapse %d", timelapse_id)
        timelapse.status = TimelapseStatus.running
        db.commit()
    finally:
        db.close()
    start(timelapse_id, interval_seconds)


async def _capture_job(timelapse_id: int) -> None:
    try:
        auto_stopped = await asyncio.to_thread(_do_sync_capture, timelapse_id)
        if auto_stopped:
            stop(timelapse_id)
    except CaptureError as exc:
        logger.warning("Capture error for timelapse %d: %s", timelapse_id, exc)
    except OSError as exc:
        logger.warning("I/O error for timelapse %d: %s", timelapse_id, exc)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error for timelapse %d: %s", timelapse_id, exc)


def _do_sync_capture(timelapse_id: int) -> bool:
    """Capture one frame. Returns True if the timelapse was auto-completed due to ended_at."""
    db = SessionLocal()
    try:
        timelapse = db.get(Timelapse, timelapse_id)
        if timelapse is None or timelapse.status != TimelapseStatus.running:
            return False

        if timelapse.ended_at and datetime.datetime.now(datetime.timezone.utc) >= timelapse.ended_at:
            logger.info("Timelapse %d reached end time — auto-completing", timelapse_id)
            timelapse.status = TimelapseStatus.completed
            db.commit()
            return True

        camera = timelapse.camera
        if camera is None:
            return False

        settings = db.get(AppSettings, 1)
        if settings is None:
            return False

        fmt = settings.capture_image_format
        if camera.connection_type == ConnectionType.network:
            data = capture_network_bytes(
                camera.rtsp_url,
                image_format=fmt,
                rtsp_transport=settings.ffmpeg_rtsp_transport,
                timeout_seconds=settings.ffmpeg_timeout_seconds,
            )
        else:
            data = capture_hardware_bytes(camera.device_index, image_format=fmt)

        ext = _FORMAT_EXT.get(fmt, "webp")
        frame_dir = os.path.join(settings.storage_path, f"timelapse_{timelapse_id}")
        usage = shutil.disk_usage(settings.storage_path)
        MIN_FREE_BYTES = 100 * 1024 * 1024  # 100 MB
        if usage.free < MIN_FREE_BYTES:
            logger.warning(
                "Low disk space: %d MB free — skipping frame for timelapse %d",
                usage.free // (1024 * 1024), timelapse_id,
            )
            return False
        os.makedirs(frame_dir, exist_ok=True)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
        filename = f"frame_{timestamp}.{ext}"
        file_path = os.path.join(frame_dir, filename)

        with open(file_path, "wb") as fh:
            fh.write(data)

        timelapse.size_bytes += len(data)
        frame = Frame(timelapse_id=timelapse_id, file_path=file_path)
        db.add(frame)
        db.commit()
        logger.debug("Captured frame for timelapse %d (%d bytes)", timelapse_id, len(data))
        return False
    finally:
        db.close()
