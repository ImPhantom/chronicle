"""Manages FFmpeg export jobs: progress tracking, concat-file building, and subprocess execution."""

import asyncio
import datetime
import logging
import os
import subprocess
import tempfile
import threading
from typing import Dict, List, Optional

from database import SessionLocal
from models.export import ExportJob, ExportStatus

logger = logging.getLogger(__name__)

# In-memory progress overlay for running jobs (DB job id → current frames_done).
_active_progress: Dict[int, int] = {}
_progress_lock = threading.Lock()


def get_live_progress(job_id: int) -> Optional[int]:
    """Return current frames_done for a running job, or None if not tracked."""
    with _progress_lock:
        return _active_progress.get(job_id)


def _set_progress(job_id: int, frames_done: int) -> None:
    with _progress_lock:
        _active_progress[job_id] = frames_done


def _clear_progress(job_id: int) -> None:
    with _progress_lock:
        _active_progress.pop(job_id, None)


def _build_concat_list(frame_paths: List[str], fps: int) -> str:
    """Write a temporary ffconcat file and return its path. Caller must delete it."""
    duration = 1.0 / fps
    fd, path = tempfile.mkstemp(prefix="chronicle_concat_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("ffconcat version 1.0\n")
            for fp in frame_paths:
                # Resolve to absolute path so FFmpeg doesn't interpret relative
                # paths relative to the temp directory where the concat file lives.
                abs_fp = os.path.abspath(fp)
                # Use forward slashes for FFmpeg cross-platform compatibility.
                safe = abs_fp.replace("\\", "/")
                fh.write(f"file '{safe}'\n")
                fh.write(f"duration {duration:.6f}\n")
    except Exception:
        os.unlink(path)
        raise
    return path


def _build_scale_filter(resolution: str, custom_resolution: Optional[str]) -> Optional[str]:
    """Return a vf scale+pad filter string, or None for 'original'."""
    if resolution == "original":
        return None
    if resolution == "custom":
        target = custom_resolution or "1920x1080"
    else:
        target = resolution
    w, h = target.split("x")
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
    )


def _build_ffmpeg_cmd(job: ExportJob, concat_path: str) -> List[str]:
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-fps_mode", "vfr",
    ]

    scale_filter = _build_scale_filter(job.resolution, job.custom_resolution)
    if scale_filter:
        cmd += ["-vf", scale_filter]

    if job.output_format == "webm":
        cmd += [
            "-c:v", "libvpx-vp9",
            "-crf", str(job.crf),
            "-b:v", "0",
            "-an",
            "-f", "webm",
        ]
    else:  # mp4
        cmd += [
            "-c:v", "libx264",
            "-crf", str(job.crf),
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-an",
            "-movflags", "+faststart",
            "-f", "mp4",
        ]

    cmd += ["-progress", "pipe:1", "-nostats", job.output_path]
    return cmd


def _parse_frame_count(line: str) -> Optional[int]:
    """Parse 'frame=N' lines from FFmpeg -progress output."""
    line = line.strip()
    if line.startswith("frame="):
        try:
            return int(line.split("=", 1)[1].strip())
        except ValueError:
            pass
    return None


def _run_export_sync(
    job_id: int,
    frame_paths: List[str],
    output_path: str,
) -> None:
    """Blocking export runner. Opens its own DB session."""
    db = SessionLocal()
    concat_path: Optional[str] = None
    try:
        job = db.get(ExportJob, job_id)
        if job is None:
            logger.error("Export job %d not found in DB", job_id)
            return

        job.status = ExportStatus.running
        db.commit()

        concat_path = _build_concat_list(frame_paths, job.output_fps)
        cmd = _build_ffmpeg_cmd(job, concat_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        logger.info("Starting FFmpeg export job %d: %s", job_id, " ".join(cmd))

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Drain stderr in a background thread to prevent pipe-buffer deadlock.
        stderr_chunks: List[str] = []

        def _drain_stderr() -> None:
            if proc.stderr:
                for line in proc.stderr:
                    stderr_chunks.append(line)

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        for line in proc.stdout:  # type: ignore[union-attr]
            count = _parse_frame_count(line)
            if count is not None:
                _set_progress(job_id, count)

        proc.wait()
        stderr_thread.join()

        # Re-fetch job to avoid stale state.
        db.expire(job)
        job = db.get(ExportJob, job_id)

        if proc.returncode != 0:
            stderr_out = "".join(stderr_chunks)
            logger.error("FFmpeg export job %d failed (rc=%d): %s", job_id, proc.returncode, stderr_out)
            job.status = ExportStatus.error
            job.error_message = stderr_out[-2000:] if stderr_out else f"FFmpeg exited with code {proc.returncode}"
        else:
            job.status = ExportStatus.completed
            job.frames_done = job.total_frames
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            logger.info("Export job %d completed successfully", job_id)

        db.commit()

    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error in export job %d", job_id)
        try:
            job = db.get(ExportJob, job_id)
            if job:
                job.status = ExportStatus.error
                job.error_message = str(exc)
                db.commit()
        except Exception:
            pass
    finally:
        _clear_progress(job_id)
        if concat_path and os.path.exists(concat_path):
            try:
                os.unlink(concat_path)
            except OSError:
                pass
        db.close()


async def start_export(
    job_id: int,
    frame_paths: List[str],
    output_path: str,
) -> None:
    """Async wrapper — runs the blocking export in a thread pool."""
    await asyncio.to_thread(_run_export_sync, job_id, frame_paths, output_path)
