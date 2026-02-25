import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import capture_manager as cm
from cleanup import delete_timelapse_files
from database import get_db
from models.camera import Camera as CameraModel
from models.timelapse import Timelapse as TimelapseModel, TimelapseStatus
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
    if timelapse.status == TimelapseStatus.running:
        cm.start(timelapse.id, timelapse.interval_seconds)
    elif timelapse.status == TimelapseStatus.pending and timelapse.started_at:
        if timelapse.started_at > datetime.datetime.now(datetime.timezone.utc):
            cm.schedule_start(timelapse.id, timelapse.started_at, timelapse.interval_seconds)
    return timelapse


@router.patch("/{timelapse_id}", response_model=Timelapse)
async def update_timelapse(
    timelapse_id: int, payload: TimelapseUpdate, db: Session = Depends(get_db)
):
    timelapse = db.get(TimelapseModel, timelapse_id)
    if timelapse is None:
        raise HTTPException(status_code=404, detail="Timelapse not found")
    old_status = timelapse.status
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(timelapse, field, value)
    db.commit()
    db.refresh(timelapse)
    new_status = timelapse.status
    if new_status != old_status:
        if new_status == TimelapseStatus.running:
            if old_status == TimelapseStatus.paused:
                cm.resume(timelapse_id)
            else:
                cm.start(timelapse_id, timelapse.interval_seconds)
        elif new_status == TimelapseStatus.paused and old_status == TimelapseStatus.running:
            cm.pause(timelapse_id)
        elif new_status == TimelapseStatus.completed:
            cm.stop(timelapse_id)
    # Re-sync the scheduled-start job whenever a pending timelapse is patched,
    # in case started_at was added or changed.
    if timelapse.status == TimelapseStatus.pending and timelapse.started_at:
        if timelapse.started_at > datetime.datetime.now(datetime.timezone.utc):
            cm.schedule_start(timelapse.id, timelapse.started_at, timelapse.interval_seconds)
        else:
            cm.stop(timelapse_id)  # started_at moved to the past — cancel stale start job
    return timelapse


@router.delete("/{timelapse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timelapse(timelapse_id: int, db: Session = Depends(get_db)):
    timelapse = db.get(TimelapseModel, timelapse_id)
    if timelapse is None:
        raise HTTPException(status_code=404, detail="Timelapse not found")
    cm.stop(timelapse_id)
    delete_timelapse_files(timelapse_id, db)
    db.delete(timelapse)
    db.commit()
