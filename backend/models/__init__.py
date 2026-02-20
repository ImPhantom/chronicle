from models.camera import Camera, ConnectionType
from models.timelapse import Timelapse, TimelapseStatus
from models.frame import Frame
from models.settings import AppSettings, RtspTransport, CaptureImageFormat

from sqlalchemy import func, select
from sqlalchemy.orm import column_property

Timelapse.__mapper__.add_property(
    "last_frame_id",
    column_property(
        select(Frame.id)
        .where(Frame.timelapse_id == Timelapse.id)
        .order_by(Frame.captured_at.desc())
        .limit(1)
        .scalar_subquery()
    ),
)

Timelapse.__mapper__.add_property(
    "frame_count",
    column_property(
        select(func.count(Frame.id)) # pylint: disable=not-callable
        .where(Frame.timelapse_id == Timelapse.id)
        .scalar_subquery()
    ),
)

__all__ = ["Camera", "ConnectionType", "Timelapse", "TimelapseStatus", "Frame",
           "AppSettings", "RtspTransport", "CaptureImageFormat"]
