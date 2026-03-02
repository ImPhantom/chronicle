import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from models.camera import ConnectionType


class CameraBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    connection_type: ConnectionType
    rtsp_url: Optional[str] = None
    device_index: Optional[int] = None
    enabled: bool = True

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not (v.startswith("rtsp://") or v.startswith("rtsps://")):
            raise ValueError("RTSP URL must begin with rtsp:// or rtsps://")
        return v

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
    name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None
    connection_type: Optional[ConnectionType] = None
    rtsp_url: Optional[str] = None
    device_index: Optional[int] = None
    enabled: Optional[bool] = None

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not (v.startswith("rtsp://") or v.startswith("rtsps://")):
            raise ValueError("RTSP URL must begin with rtsp:// or rtsps://")
        return v

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

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not (v.startswith("rtsp://") or v.startswith("rtsps://")):
            raise ValueError("RTSP URL must begin with rtsp:// or rtsps://")
        return v

    @model_validator(mode="after")
    def validate_connection_fields(self) -> "TestCaptureRequest":
        if self.connection_type == ConnectionType.network and not self.rtsp_url:
            raise ValueError("rtsp_url is required when connection_type is 'network'")
        if self.connection_type == ConnectionType.hardware and self.device_index is None:
            raise ValueError("device_index is required when connection_type is 'hardware'")
        return self
