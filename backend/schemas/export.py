import datetime
import os
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

OutputFormat = Literal["webm", "mp4"]
Resolution   = Literal["original", "1920x1080", "1280x720", "640x360", "custom"]


class ExportRequest(BaseModel):
    output_format:     OutputFormat = "webm"
    output_fps:        int          = Field(default=30, ge=1, le=120)
    resolution:        Resolution   = "original"
    custom_resolution: Optional[str] = None   # "WxH", only when resolution=="custom"
    crf:               int          = Field(default=28, ge=0, le=63)
    smoothing:         Optional[Literal["blend", "interpolate"]] = None
    target_duration:   Optional[float] = None  # informational; FPS already computed client-side
    stabilization:     bool = False
    denoising:         bool = False
    color_correction:  Optional[Literal["auto", "manual"]] = None
    brightness:        Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    contrast:          Optional[float] = Field(default=None, ge=0.5, le=2.0)
    saturation:        Optional[float] = Field(default=None, ge=0.0, le=2.0)

    @model_validator(mode="after")
    def validate_custom_resolution(self) -> "ExportRequest":
        if self.resolution == "custom":
            if not self.custom_resolution or not re.match(r"^\d+x\d+$", self.custom_resolution):
                raise ValueError("custom_resolution must be in 'WxH' format (e.g. '1920x1080')")
        if self.color_correction == "manual":
            missing = [f for f in ("brightness", "contrast", "saturation") if getattr(self, f) is None]
            if missing:
                raise ValueError(f"color_correction='manual' requires: {', '.join(missing)}")
        return self


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
    smoothing:        Optional[str]   = None
    stabilization:    bool            = False
    denoising:        bool            = False
    color_correction: Optional[str]   = None
    brightness:       Optional[float] = None
    contrast:         Optional[float] = None
    saturation:       Optional[float] = None

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
            smoothing=job.smoothing,
            stabilization=job.stabilization,
            denoising=job.denoising,
            color_correction=job.color_correction,
            brightness=job.brightness,
            contrast=job.contrast,
            saturation=job.saturation,
        )
