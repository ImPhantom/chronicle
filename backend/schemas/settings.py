from typing import Annotated, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

from models.settings import CaptureImageFormat, RtspTransport


class AppSettingsBase(BaseModel):
    timezone: str = "UTC"
    storage_path: str = "./data"
    max_storage_gb: Optional[float] = None
    ffmpeg_timeout_seconds: Annotated[int, Field(gt=0)] = 10
    ffmpeg_rtsp_transport: RtspTransport = RtspTransport.tcp
    capture_image_format: CaptureImageFormat = CaptureImageFormat.webp
    capture_image_quality: Annotated[int, Field(ge=1, le=100)] = 85
    default_capture_interval_seconds: Annotated[int, Field(gt=0)] = 60
    max_frames_per_timelapse: Optional[int] = None
    retention_days: Optional[int] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v == "UTC":
            return v
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: {v!r}")
        return v


class AppSettings(AppSettingsBase):
    id: int
    model_config = {"from_attributes": True}


class AppSettingsUpdate(BaseModel):
    timezone: Optional[str] = None
    storage_path: Optional[str] = None
    max_storage_gb: Optional[float] = None
    ffmpeg_timeout_seconds: Optional[Annotated[int, Field(gt=0)]] = None
    ffmpeg_rtsp_transport: Optional[RtspTransport] = None
    capture_image_format: Optional[CaptureImageFormat] = None
    capture_image_quality: Optional[Annotated[int, Field(ge=1, le=100)]] = None
    default_capture_interval_seconds: Optional[Annotated[int, Field(gt=0)]] = None
    max_frames_per_timelapse: Optional[int] = None
    retention_days: Optional[int] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "UTC":
            return v
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: {v!r}")
        return v
