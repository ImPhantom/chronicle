import datetime
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base, UTCDateTime


class ExportStatus(str, enum.Enum):
    pending   = "pending"
    running   = "running"
    completed = "completed"
    error     = "error"


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id:                Mapped[int]                      = mapped_column(primary_key=True, index=True)
    timelapse_id:      Mapped[int]                      = mapped_column(ForeignKey("timelapses.id", ondelete="CASCADE"), nullable=False, index=True)
    status:            Mapped[ExportStatus]             = mapped_column(Enum(ExportStatus), default=ExportStatus.pending, nullable=False, index=True)
    output_format:     Mapped[str]                      = mapped_column(String, nullable=False)   # "webm" | "mp4"
    output_fps:        Mapped[int]                      = mapped_column(Integer, nullable=False)
    resolution:        Mapped[str]                      = mapped_column(String, nullable=False)   # "original" | "1920x1080" | ...
    custom_resolution: Mapped[str | None]               = mapped_column(String, nullable=True)
    crf:               Mapped[int]                      = mapped_column(Integer, nullable=False)
    total_frames:      Mapped[int]                      = mapped_column(Integer, nullable=False)
    frames_done:       Mapped[int]                      = mapped_column(Integer, nullable=False, default=0, server_default="0")
    output_path:       Mapped[str | None]               = mapped_column(String, nullable=True)
    error_message:     Mapped[str | None]               = mapped_column(String, nullable=True)
    created_at:        Mapped[datetime.datetime]        = mapped_column(UTCDateTime, server_default=func.now(), nullable=False)  # pylint: disable=not-callable
    completed_at:      Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
