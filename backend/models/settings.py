import enum

from sqlalchemy import CheckConstraint, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class RtspTransport(str, enum.Enum):
    tcp = "tcp"
    udp = "udp"
    http = "http"


class CaptureImageFormat(str, enum.Enum):
    webp = "webp"
    jpeg = "jpeg"
    png = "png"


class AppSettings(Base):
    __tablename__ = "app_settings"
    __table_args__ = (CheckConstraint("id = 1", name="ck_app_settings_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    timezone: Mapped[str] = mapped_column(String, nullable=False, default="UTC")
    storage_path: Mapped[str] = mapped_column(String, nullable=False, default="./data")
    max_storage_gb: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    ffmpeg_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    ffmpeg_rtsp_transport: Mapped[str] = mapped_column(String, nullable=False, default="tcp")
    capture_image_format: Mapped[str] = mapped_column(String, nullable=False, default="webp")
    capture_image_quality: Mapped[int] = mapped_column(Integer, nullable=False, default=85)
    default_capture_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    max_frames_per_timelapse: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
