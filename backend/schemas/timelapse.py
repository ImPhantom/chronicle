import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from models.timelapse import TimelapseStatus


class TimelapseBase(BaseModel):
    camera_id: int
    name: Annotated[str, Field(min_length=1, max_length=100)]
    interval_seconds: Annotated[int, Field(gt=0)]
    status: TimelapseStatus = TimelapseStatus.pending
    started_at: Optional[datetime.datetime] = None
    ended_at: Optional[datetime.datetime] = None


class TimelapseCreate(TimelapseBase):
    pass


class TimelapseUpdate(BaseModel):
    name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None
    interval_seconds: Optional[Annotated[int, Field(gt=0)]] = None
    status: Optional[TimelapseStatus] = None
    started_at: Optional[datetime.datetime] = None
    ended_at: Optional[datetime.datetime] = None


class Timelapse(TimelapseBase):
    id: int
    created_at: datetime.datetime
    last_frame_id: Optional[int] = None
    frame_count: int = 0
    size_bytes: int = 0

    model_config = {"from_attributes": True}
