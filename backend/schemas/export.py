import datetime
import os
from typing import Literal, Optional

from pydantic import BaseModel, Field

OutputFormat = Literal["webm", "mp4"]
Resolution   = Literal["original", "1920x1080", "1280x720", "640x360", "custom"]


class ExportRequest(BaseModel):
    output_format:     OutputFormat = "webm"
    output_fps:        int          = Field(default=30, ge=1, le=120)
    resolution:        Resolution   = "original"
    custom_resolution: Optional[str] = None   # "WxH", only when resolution=="custom"
    crf:               int          = Field(default=28, ge=0, le=63)


class ExportJobResponse(BaseModel):
    id:            int
    timelapse_id:  int
    status:        str
    output_format: OutputFormat
    output_fps:    int
    resolution:    str
    crf:           int
    total_frames:  int
    frames_done:   int
    progress_pct:  float
    output_file:      Optional[str] = None
    file_size_bytes:  Optional[int] = None
    error_message:    Optional[str] = None
    created_at:    datetime.datetime
    completed_at:  Optional[datetime.datetime] = None

    @classmethod
    def from_job(cls, job, frames_done_override: Optional[int] = None) -> "ExportJobResponse":
        frames_done = frames_done_override if frames_done_override is not None else job.frames_done
        total = job.total_frames or 1
        progress_pct = round(frames_done / total * 100, 1)
        output_file = os.path.basename(job.output_path) if job.output_path else None
        return cls(
            id=job.id,
            timelapse_id=job.timelapse_id,
            status=job.status.value,
            output_format=job.output_format,
            output_fps=job.output_fps,
            resolution=job.resolution,
            crf=job.crf,
            total_frames=job.total_frames,
            frames_done=frames_done,
            progress_pct=progress_pct,
            output_file=output_file,
            file_size_bytes=job.file_size_bytes,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
