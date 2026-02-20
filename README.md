# Chronicle

*also formerly 'Netlapse'*

Timelapse management for network and USB cameras.

> [!NOTE]
> __I want to note that this project is not entirely 'vibe-coded'__ 
> 
> I do know how to program and think logically, unlike the ol "script kiddos"

## Overview

Chronicle captures RTSP streams and local hardware camera feeds on a schedule, storing each frame as a WebP image. A web UI lets you browse and manage timelapses, preview the latest capture, and control capture state. Planned: render any timelapse's frames into a downloadable MP4 or WebM video using FFmpeg.

## Features

### Working today

- **Camera management** — add and manage network (RTSP) and local USB cameras
- **Live test capture** — preview a frame before adding a camera
- **Frame browser** — view captured frames and last-frame preview per timelapse
- **Timelapse status control** — start, pause, resume, and complete timelapses
- **App-wide settings** — configure storage path, FFmpeg options, image quality, and more

### In progress / planned

- **Scheduled capture loop** — periodic frame capture via APScheduler
- **Video rendering** — render a timelapse's frames into a downloadable MP4/WebM via FFmpeg
- **Docker packaging** — single container wrapping frontend and backend

## Architecture

```
chronicle/
├── backend/    # Python + FastAPI — REST API, scheduling, FFmpeg, SQLite
└── frontend/   # Vite + Vue 3 — management UI
```

The frontend calls the FastAPI backend via a Vite dev proxy.

## Getting Started

### Backend

```bash
cd backend

pip install -r requirements.txt      # Install dependencies
uvicorn main:app --reload             # Start dev server (port 8000)
```

### Frontend

```bash
cd frontend

bun install       # Install dependencies
bun run dev       # Start Vite dev server
bun run build     # Type-check then bundle
bun run preview   # Preview production build
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend framework | Vue 3 + TypeScript |
| Frontend build | Vite + Bun |
| UI components | shadcn-vue (reka-ui) + Tailwind CSS v4 |
| Icons | Phosphor Icons, Lucide |
| Utilities | VueUse, vue-router |
| Backend framework | FastAPI (Python) |
| Database | SQLite via SQLAlchemy |
| Validation | Pydantic |
| Image capture | FFmpeg subprocess, OpenCV |
| Scheduling | APScheduler (planned) |
| Deployment | Docker (planned) |
