import datetime
from typing import Optional

from pydantic import BaseModel

from models.timelapse import TimelapseStatus


class TimelapseBase(BaseModel):
    camera_id: int
    name: str
    interval_seconds: int
    status: TimelapseStatus = TimelapseStatus.pending
    started_at: Optional[datetime.datetime] = None
    ended_at: Optional[datetime.datetime] = None


class TimelapseCreate(TimelapseBase):
    pass


class TimelapseUpdate(BaseModel):
    name: Optional[str] = None
    interval_seconds: Optional[int] = None
    status: Optional[TimelapseStatus] = None
    started_at: Optional[datetime.datetime] = None
    ended_at: Optional[datetime.datetime] = None


class Timelapse(TimelapseBase):
    id: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
