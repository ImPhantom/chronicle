import datetime
import os
import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import export_manager
from database import get_db
from models.export import ExportJob, ExportStatus
from models.frame import Frame
from models.settings import AppSettings
from models.timelapse import Timelapse
from schemas.export import ExportJobResponse, ExportRequest

router = APIRouter(prefix="/exports", tags=["exports"])

_CUSTOM_RES_RE = re.compile(r"^\d+x\d+$")


@router.post(
    "/timelapses/{timelapse_id}",
    response_model=ExportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_export(
    timelapse_id: int,
    payload: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    timelapse = db.get(Timelapse, timelapse_id)
    if timelapse is None:
        raise HTTPException(status_code=404, detail="Timelapse not found")

    frames = (
        db.query(Frame)
        .filter(Frame.timelapse_id == timelapse_id)
        .order_by(Frame.captured_at.asc())
        .all()
    )
    if not frames:
        raise HTTPException(status_code=422, detail="Timelapse has no frames to export")

    if payload.resolution == "custom":
        if not payload.custom_resolution or not _CUSTOM_RES_RE.match(payload.custom_resolution):
            raise HTTPException(
                status_code=422,
                detail="custom_resolution must be in 'WxH' format (e.g. '1920x1080')",
            )

    settings = db.get(AppSettings, 1)
    storage_path = settings.storage_path if settings else "./data"

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    filename = f"timelapse_{timelapse_id}_{timestamp}.{payload.output_format}"
    output_path = os.path.join(storage_path, "exports", filename)

    job = ExportJob(
        timelapse_id=timelapse_id,
        status=ExportStatus.pending,
        output_format=payload.output_format,
        output_fps=payload.output_fps,
        resolution=payload.resolution,
        custom_resolution=payload.custom_resolution,
        crf=payload.crf,
        total_frames=len(frames),
        frames_done=0,
        output_path=output_path,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    frame_paths = [f.file_path for f in frames]
    background_tasks.add_task(export_manager.start_export, job.id, frame_paths, output_path)

    return ExportJobResponse.from_job(job)


@router.get("/{job_id}/status", response_model=ExportJobResponse)
def get_export_status(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ExportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Export job not found")

    frames_done_override = None
    if job.status == ExportStatus.running:
        live = export_manager.get_live_progress(job_id)
        if live is not None:
            frames_done_override = live

    return ExportJobResponse.from_job(job, frames_done_override)


@router.get("/{job_id}/download")
def download_export(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ExportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Export job not found")
    if job.status != ExportStatus.completed:
        raise HTTPException(status_code=409, detail="Export is not yet complete")
    if not job.output_path or not os.path.isfile(job.output_path):
        raise HTTPException(status_code=404, detail="Export file not found on disk")

    media_type = "video/webm" if job.output_format == "webm" else "video/mp4"
    filename = os.path.basename(job.output_path)
    return FileResponse(
        path=job.output_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/list/{timelapse_id}")
def list_exports_for_timelapse(timelapse_id: int, db: Session = Depends(get_db)):
	timelapse = db.get(Timelapse, timelapse_id)
	if timelapse is None:
		raise HTTPException(status_code=404, detail="Timelapse not found")

	jobs = db.query(ExportJob).filter(ExportJob.timelapse_id == timelapse_id).order_by(ExportJob.created_at.desc()).all()
	return [ExportJobResponse.from_job(job) for job in jobs]
