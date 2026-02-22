import datetime
import enum

from sqlalchemy import Boolean, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, UTCDateTime


class ConnectionType(str, enum.Enum):
    network = "network"
    hardware = "hardware"


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    connection_type: Mapped[ConnectionType] = mapped_column(
        Enum(ConnectionType), nullable=False
    )
    rtsp_url: Mapped[str | None] = mapped_column(String, nullable=True)
    device_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False # pylint: disable=not-callable
    )

    timelapses: Mapped[list["Timelapse"]] = relationship(  # noqa: F821
        "Timelapse", back_populates="camera", cascade="all, delete-orphan"
    )
