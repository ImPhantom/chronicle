import os
import shutil
from sqlalchemy.orm import Session
from models.export import ExportJob
from models.frame import Frame


def delete_timelapse_files(timelapse_id: int, db: Session) -> None:
    """Delete the frame directory and all export files for a timelapse."""
    # Delete export files
    export_jobs = db.query(ExportJob).filter(ExportJob.timelapse_id == timelapse_id).all()
    for job in export_jobs:
        if job.output_path and os.path.isfile(job.output_path):
            try:
                os.remove(job.output_path)
            except OSError:
                pass

    # Delete the frame directory (derived from first frame's path)
    first_frame = db.query(Frame).filter(Frame.timelapse_id == timelapse_id).first()
    if first_frame:
        frame_dir = os.path.dirname(first_frame.file_path)
        if os.path.isdir(frame_dir):
            try:
                shutil.rmtree(frame_dir)
            except OSError:
                pass
