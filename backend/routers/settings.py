import shutil

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.settings import AppSettings as AppSettingsModel
from schemas.settings import AppSettings, AppSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


class StorageStats(BaseModel):
    total_bytes: int
    used_bytes: int
    free_bytes: int


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
    settings = _ensure_settings_row(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/storage", response_model=StorageStats)
def read_storage(settings: AppSettingsModel = Depends(get_settings)):
    usage = shutil.disk_usage(settings.storage_path)
    return StorageStats(total_bytes=usage.total, used_bytes=usage.used, free_bytes=usage.free)
