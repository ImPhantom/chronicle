import logging
import os
import shutil
from sqlalchemy.orm import Session
from models.export import ExportJob
from models.frame import Frame

logger = logging.getLogger(__name__)


def delete_timelapse_files(timelapse_id: int, db: Session) -> None:
    """Delete the frame directory and all export files for a timelapse."""
    # Delete export files
    export_jobs = db.query(ExportJob).filter(ExportJob.timelapse_id == timelapse_id).all()
    export_files = [j for j in export_jobs if j.output_path and os.path.isfile(j.output_path)]
    if export_files:
        logger.info("Removing %d export file(s) for timelapse %d", len(export_files), timelapse_id)
    for job in export_jobs:
        if job.output_path and os.path.isfile(job.output_path):
            try:
                os.remove(job.output_path)
            except OSError as exc:
                logger.warning("Failed to remove export file %s: %s", job.output_path, exc)

    # Delete the frame directory (derived from first frame's path)
    first_frame = db.query(Frame).filter(Frame.timelapse_id == timelapse_id).first()
    if first_frame:
        frame_dir = os.path.dirname(first_frame.file_path)
        if os.path.isdir(frame_dir):
            logger.info("Removing frame directory %s", frame_dir)
            try:
                shutil.rmtree(frame_dir)
            except OSError as exc:
                logger.warning("Failed to remove frame directory %s: %s", frame_dir, exc)
