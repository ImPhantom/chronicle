import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, UTCDateTime


class Frame(Base):
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timelapse_id: Mapped[int] = mapped_column(
        ForeignKey("timelapses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    captured_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False # pylint: disable=not-callable
    )

    timelapse: Mapped["Timelapse"] = relationship("Timelapse", back_populates="frames")  # noqa: F821
