import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models.frame import Frame as FrameModel
from models.timelapse import Timelapse as TimelapseModel
from schemas.frame import Frame, FrameCreate, FrameUpdate

router = APIRouter(prefix="/frames", tags=["frames"])


@router.get("", response_model=List[Frame])
def list_frames(
    timelapse_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(FrameModel).order_by(FrameModel.captured_at.asc())
    if timelapse_id is not None:
        query = query.filter(FrameModel.timelapse_id == timelapse_id)
    return query.all()

@router.get("/{frame_id}/image")
def get_frame_image(frame_id: int, db: Session = Depends(get_db)):
    frame = db.get(FrameModel, frame_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    if not os.path.isfile(frame.file_path):
        raise HTTPException(status_code=404, detail="Frame image file not found on disk")
    return FileResponse(frame.file_path)


@router.get("/{frame_id}", response_model=Frame)
def get_frame(frame_id: int, db: Session = Depends(get_db)):
    frame = db.get(FrameModel, frame_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    return frame


@router.post("", response_model=Frame, status_code=status.HTTP_201_CREATED)
def create_frame(payload: FrameCreate, db: Session = Depends(get_db)):
    if db.get(TimelapseModel, payload.timelapse_id) is None:
        raise HTTPException(status_code=404, detail="Timelapse not found")
    data = payload.model_dump()
    if data.get("captured_at") is None:
        data.pop("captured_at")
    frame = FrameModel(**data)
    db.add(frame)
    db.commit()
    db.refresh(frame)
    return frame


@router.patch("/{frame_id}", response_model=Frame)
def update_frame(frame_id: int, payload: FrameUpdate, db: Session = Depends(get_db)):
    frame = db.get(FrameModel, frame_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(frame, field, value)
    db.commit()
    db.refresh(frame)
    return frame


@router.delete("/{frame_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_frame(frame_id: int, db: Session = Depends(get_db)):
    frame = db.get(FrameModel, frame_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    db.delete(frame)
    db.commit()
