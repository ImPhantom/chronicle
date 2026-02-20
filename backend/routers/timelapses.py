from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.camera import Camera as CameraModel
from models.timelapse import Timelapse as TimelapseModel
from schemas.timelapse import Timelapse, TimelapseCreate, TimelapseUpdate

router = APIRouter(prefix="/timelapses", tags=["timelapses"])


@router.get("", response_model=List[Timelapse])
def list_timelapses(
    camera_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(TimelapseModel)
    if camera_id is not None:
        query = query.filter(TimelapseModel.camera_id == camera_id)
    return query.all()


@router.get("/{timelapse_id}", response_model=Timelapse)
def get_timelapse(timelapse_id: int, db: Session = Depends(get_db)):
    timelapse = db.get(TimelapseModel, timelapse_id)
    if timelapse is None:
        raise HTTPException(status_code=404, detail="Timelapse not found")
    return timelapse


@router.post("", response_model=Timelapse, status_code=status.HTTP_201_CREATED)
def create_timelapse(payload: TimelapseCreate, db: Session = Depends(get_db)):
    if db.get(CameraModel, payload.camera_id) is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    timelapse = TimelapseModel(**payload.model_dump())
    db.add(timelapse)
    db.commit()
    db.refresh(timelapse)
    return timelapse


@router.patch("/{timelapse_id}", response_model=Timelapse)
def update_timelapse(
    timelapse_id: int, payload: TimelapseUpdate, db: Session = Depends(get_db)
):
    timelapse = db.get(TimelapseModel, timelapse_id)
    if timelapse is None:
        raise HTTPException(status_code=404, detail="Timelapse not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(timelapse, field, value)
    db.commit()
    db.refresh(timelapse)
    return timelapse


@router.delete("/{timelapse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timelapse(timelapse_id: int, db: Session = Depends(get_db)):
    timelapse = db.get(TimelapseModel, timelapse_id)
    if timelapse is None:
        raise HTTPException(status_code=404, detail="Timelapse not found")
    db.delete(timelapse)
    db.commit()
