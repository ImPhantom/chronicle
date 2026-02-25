from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel as _BaseModel
from sqlalchemy.orm import Session

import capture_manager as cm
from cleanup import delete_timelapse_files
from capture import (
    CaptureError,
    _FORMAT_MEDIA_TYPE,
    capture_hardware_bytes,
    capture_network_bytes,
)
from database import get_db
from models.camera import Camera as CameraModel
from models.settings import AppSettings as AppSettingsModel
from routers.settings import get_settings
from schemas.camera import Camera, CameraCreate, CameraUpdate, TestCaptureRequest

router = APIRouter(prefix="/cameras", tags=["cameras"])


class HardwareCameraInfo(_BaseModel):
    index: int
    name: str


@router.get("", response_model=List[Camera])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(CameraModel).all()


@router.get("/hardware", response_model=List[HardwareCameraInfo])
def list_hardware_cameras():
    try:
        from cv2_enumerate_cameras import enumerate_cameras
        return [
            HardwareCameraInfo(index=cam.index, name=cam.name or f"Camera {cam.index}")
            for cam in enumerate_cameras()
        ]
    except Exception:
        return []


@router.post("/test-capture")
def test_capture(
    payload: TestCaptureRequest,
    settings: AppSettingsModel = Depends(get_settings),
):
    if payload.connection_type == "network":
        return _capture_network(payload.rtsp_url, settings)
    return _capture_hardware(payload.device_index, settings)


def _capture_network(rtsp_url: str, settings: AppSettingsModel) -> Response:
    fmt = settings.capture_image_format
    try:
        data = capture_network_bytes(
            rtsp_url,
            image_format=fmt,
            rtsp_transport=settings.ffmpeg_rtsp_transport,
            timeout_seconds=settings.ffmpeg_timeout_seconds,
        )
    except CaptureError as exc:
        raise HTTPException(500, str(exc)) from exc
    return Response(content=data, media_type=_FORMAT_MEDIA_TYPE.get(fmt, "image/webp"))


def _capture_hardware(device_index: int, settings: AppSettingsModel) -> Response:
    fmt = settings.capture_image_format
    try:
        data = capture_hardware_bytes(device_index, image_format=fmt)
    except CaptureError as exc:
        raise HTTPException(500, str(exc)) from exc
    return Response(content=data, media_type=_FORMAT_MEDIA_TYPE.get(fmt, "image/webp"))


@router.get("/{camera_id}", response_model=Camera)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = db.get(CameraModel, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.post("", response_model=Camera, status_code=status.HTTP_201_CREATED)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    camera = CameraModel(**payload.model_dump())
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


@router.patch("/{camera_id}", response_model=Camera)
def update_camera(camera_id: int, payload: CameraUpdate, db: Session = Depends(get_db)):
    camera = db.get(CameraModel, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(camera, field, value)
    db.commit()
    db.refresh(camera)
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = db.get(CameraModel, camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    for timelapse in camera.timelapses:
        cm.stop(timelapse.id)
        delete_timelapse_files(timelapse.id, db)
    db.delete(camera)
    db.commit()
