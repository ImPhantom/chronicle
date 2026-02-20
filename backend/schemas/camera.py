import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from models.camera import ConnectionType


class CameraBase(BaseModel):
    name: str
    connection_type: ConnectionType
    rtsp_url: Optional[str] = None
    device_index: Optional[int] = None
    enabled: bool = True

    @model_validator(mode="after")
    def validate_connection_fields(self) -> "CameraBase":
        if self.connection_type == ConnectionType.network and not self.rtsp_url:
            raise ValueError("rtsp_url is required when connection_type is 'network'")
        if self.connection_type == ConnectionType.hardware and self.device_index is None:
            raise ValueError("device_index is required when connection_type is 'hardware'")
        return self


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    connection_type: Optional[ConnectionType] = None
    rtsp_url: Optional[str] = None
    device_index: Optional[int] = None
    enabled: Optional[bool] = None

    @model_validator(mode="after")
    def validate_connection_fields(self) -> "CameraUpdate":
        # Only validate if connection_type is explicitly being set in this PATCH
        if self.connection_type == ConnectionType.network and not self.rtsp_url:
            raise ValueError("rtsp_url is required when connection_type is 'network'")
        if self.connection_type == ConnectionType.hardware and self.device_index is None:
            raise ValueError("device_index is required when connection_type is 'hardware'")
        return self


class Camera(CameraBase):
    id: int
    created_at: datetime.datetime
    model_config = {"from_attributes": True}


class TestCaptureRequest(BaseModel):
    connection_type: ConnectionType
    rtsp_url: Optional[str] = None
    device_index: Optional[int] = None

    @model_validator(mode="after")
    def validate_connection_fields(self) -> "TestCaptureRequest":
        if self.connection_type == ConnectionType.network and not self.rtsp_url:
            raise ValueError("rtsp_url is required when connection_type is 'network'")
        if self.connection_type == ConnectionType.hardware and self.device_index is None:
            raise ValueError("device_index is required when connection_type is 'hardware'")
        return self
