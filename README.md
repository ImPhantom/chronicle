# Chronicle

This is an application that allows a user to create and manage timelapses for any network camera. Then eventually turn those timelapses into beautiful videos.

## Projected Stack

### Frontend
- Vite (Vue)
- shadcn-vue, tailwind
- Calls to FastAPI

### Backend
- Python + FastAPI
- APScheduler (schedules capture jobs)
- SQLAlchemy + SQLite (persistent data (cameras, timelapses))
- runs/manages FFMPEG subprocess to capture RTSP -> WebP

### Docker
- Wraps up both into one neat lil package