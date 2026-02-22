import datetime
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, UTCDateTime


class TimelapseStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    completed = "completed"


class Timelapse(Base):
    __tablename__ = "timelapses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    camera_id: Mapped[int] = mapped_column(
        ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TimelapseStatus] = mapped_column(
        Enum(TimelapseStatus), default=TimelapseStatus.pending, nullable=False
    )
    started_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    ended_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False # pylint: disable=not-callable
    )

    camera: Mapped["Camera"] = relationship("Camera", back_populates="timelapses")  # noqa: F821
    frames: Mapped[list["Frame"]] = relationship(  # noqa: F821
        "Frame", back_populates="timelapse", cascade="all, delete-orphan"
    )
