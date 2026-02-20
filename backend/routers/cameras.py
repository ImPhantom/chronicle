import subprocess
from typing import List

import cv2
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel as _BaseModel
from sqlalchemy.orm import Session

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
    return _capture_hardware(payload.device_index)


_FORMAT_VCODEC = {
    "webp": "webp",
    "jpeg": "mjpeg",
    "png": "png",
}

_FORMAT_MEDIA_TYPE = {
    "webp": "image/webp",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


def _capture_network(rtsp_url: str, settings: AppSettingsModel) -> Response:
    fmt = settings.capture_image_format
    vcodec = _FORMAT_VCODEC.get(fmt, "webp")
    media_type = _FORMAT_MEDIA_TYPE.get(fmt, "image/webp")
    timeout = settings.ffmpeg_timeout_seconds

    cmd = [
        "ffmpeg",
        "-rtsp_transport", settings.ffmpeg_rtsp_transport,
        "-i", rtsp_url,
        "-frames:v", "1",
        "-f", "image2pipe",
        "-vcodec", vcodec,
        "pipe:1",
    ]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, f"FFmpeg timed out after {timeout}s")
    except FileNotFoundError:
        raise HTTPException(500, "FFmpeg not found on this system")
    if result.returncode != 0 or not result.stdout:
        raise HTTPException(500, "FFmpeg failed to capture a frame")
    return Response(content=result.stdout, media_type=media_type)


def _capture_hardware(device_index: int) -> Response:
    cap = cv2.VideoCapture(device_index)
    try:
        if not cap.isOpened():
            raise HTTPException(500, f"Could not open hardware camera at index {device_index}")
        ok, frame = cap.read()
        if not ok or frame is None:
            raise HTTPException(500, "Failed to read frame from hardware camera")
        encode_ok, buf = cv2.imencode(".webp", frame)
        if not encode_ok:
            raise HTTPException(500, "Failed to encode frame as WebP")
        return Response(content=buf.tobytes(), media_type="image/webp")
    finally:
        cap.release()


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
    db.delete(camera)
    db.commit()
