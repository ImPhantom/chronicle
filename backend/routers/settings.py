import logging
import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models.export import ExportJob, ExportStatus
from models.settings import AppSettings as AppSettingsModel
from models.timelapse import Timelapse as TimelapseModel
from schemas.settings import AppSettings, AppSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger(__name__)


class TimelapseStorageItem(BaseModel):
    timelapse_id: int
    frames_size_bytes: int
    exports_size_bytes: int


class StorageStats(BaseModel):
    total_bytes: int
    used_bytes: int
    free_bytes: int
    timelapse_breakdown: List[TimelapseStorageItem]


def _ensure_settings_row(db: Session) -> AppSettingsModel:
    settings = db.get(AppSettingsModel, 1)
    if settings is None:
        settings = AppSettingsModel(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def get_settings(db: Session = Depends(get_db)) -> AppSettingsModel:
    return _ensure_settings_row(db)


@router.get("", response_model=AppSettings)
def read_settings(settings: AppSettingsModel = Depends(get_settings)):
    return settings


@router.patch("", response_model=AppSettings)
def update_settings(payload: AppSettingsUpdate, db: Session = Depends(get_db)):
    field_dict = payload.model_dump(exclude_unset=True)
    if "storage_path" in field_dict and not os.path.isdir(field_dict["storage_path"]):
        raise HTTPException(status_code=422, detail="storage_path does not exist or is not a directory")
    settings = _ensure_settings_row(db)
    for field, value in field_dict.items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    logger.info("Settings updated: %r", field_dict)
    return settings


@router.get("/storage", response_model=StorageStats)
def read_storage(settings: AppSettingsModel = Depends(get_settings), db: Session = Depends(get_db)):
    try:
        usage = shutil.disk_usage(settings.storage_path)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Storage path inaccessible: {e}")

    rows = db.execute(
        select(
            TimelapseModel.id,
            TimelapseModel.size_bytes,
            func.coalesce(func.sum(ExportJob.file_size_bytes), 0),
        )
        .outerjoin(
            ExportJob,
            (ExportJob.timelapse_id == TimelapseModel.id)
            & (ExportJob.status == ExportStatus.completed)
            & ExportJob.file_size_bytes.isnot(None),
        )
        .group_by(TimelapseModel.id)
    ).all()

    breakdown = [
        TimelapseStorageItem(
            timelapse_id=r[0],
            frames_size_bytes=r[1],
            exports_size_bytes=r[2],
        )
        for r in rows
    ]

    return StorageStats(
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        timelapse_breakdown=breakdown,
    )
