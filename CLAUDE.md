# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chronicle is a timelapse management app for network and USB cameras. It captures RTSP streams and hardware camera feeds as WebP images via FFmpeg, stores metadata in SQLite, presents a management UI, and will render timelapse frames into downloadable video files.

## Architecture

```
chronicle/
├── backend/        # Python + FastAPI
│   ├── routers/    # FastAPI route handlers
│   ├── schemas/    # Pydantic request/response schemas
│   └── models/     # SQLAlchemy ORM models
└── frontend/       # Vite + Vue 3 + TypeScript
```

### Backend (Python + FastAPI)

- **FastAPI** — HTTP API server
- **SQLAlchemy + SQLite** — persistent storage for cameras and timelapse metadata
- **Pydantic** — request/response schema validation
- **FFmpeg** subprocess — captures RTSP streams and hardware cameras to WebP images
- **OpenCV** (`opencv-python-headless`, `cv2-enumerate-cameras`) — hardware camera enumeration and capture
- **APScheduler** — scheduled capture jobs (planned; not yet in `requirements.txt`)
- Entry point: `backend/main.py`
- Dependencies: `backend/requirements.txt`

### Frontend (Vite + Vue 3)

- **Vue 3** with TypeScript
- **shadcn-vue (reka-ui) + Tailwind CSS v4** — UI components and styling
- **vue-router** — client-side routing
- **@phosphor-icons/vue** + **lucide-vue-next** — icon libraries
- **@vueuse/core** — composition utilities
- **Pinia** — state management (not yet installed)
- Entry point: `frontend/src/main.ts`
- Package manager: **Bun** (use `bun` not `npm`)

The frontend will call the FastAPI backend; configure a Vite dev proxy in `frontend/vite.config.ts` when the API is ready.

### Deployment

Both services will be wrapped into a single Docker container.

## Commands

### Frontend

```bash
cd frontend

bun install          # Install dependencies
bun run dev          # Start Vite dev server
bun run build        # Type-check (vue-tsc) then bundle
bun run preview      # Preview production build
```

### Backend

```bash
cd backend

pip install -r requirements.txt   # Install dependencies
uvicorn main:app --reload          # Start FastAPI dev server (port 8000 by default)
```
