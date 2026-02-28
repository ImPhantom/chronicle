import datetime
from typing import Optional

from pydantic import BaseModel


class FrameBase(BaseModel):
    timelapse_id: int
    file_path: str
    captured_at: Optional[datetime.datetime] = None


class FrameCreate(FrameBase):
    pass


class FrameUpdate(BaseModel):
    file_path: Optional[str] = None


class Frame(FrameBase):
    id: int
    captured_at: datetime.datetime

    model_config = {"from_attributes": True}


class FrameListResponse(BaseModel):
    frames: list[Frame]
    total: int
    offset: int
    limit: int
