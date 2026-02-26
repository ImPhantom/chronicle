# Chronicle

*formerly 'Netlapse'*

Timelapse management for network and USB cameras.

> [!NOTE]
> __I want to note that this project is not entirely 'vibe-coded'__
>
> I do know how to program and think logically, unlike the ol "script kiddos"

## Overview

This is a simple self-hosted app that allows you to create timelapses using hardware/network cameras (from IP cameras to $15 USB webcams). 

It captures frames from the camera on a schedule, storing each frame as a WebP image. A web UI then lets you browse and manage timelapses, preview the latest capture, control capture state, aswell as "Export" the timelapse frames into a downloadable MP4 or WebM file via FFmpeg.

## Features

- **Camera management** — add and manage network (RTSP) and local hardware cameras
- **Live test capture** — preview a frame before committing to a camera
- **Scheduled capture** — periodic frame capture via APScheduler at a configurable interval
- **Timelapse status control** — start, pause, resume, and complete timelapses
- **Scheduled auto-start** — set a future UTC time for a timelapse to begin automatically
- **Video export** — render frames into a downloadable MP4 or WebM using FFmpeg, with live progress tracking
- **Storage overview** — disk usage breakdown per timelapse
- **App-wide settings** — configure storage path, FFmpeg options, image quality, capture interval, and timezone

## Architecture

```
chronicle/
├── backend/    # Python + FastAPI — REST API, scheduling, FFmpeg, SQLite
└── frontend/   # Vite + Vue 3 — management UI
```

The frontend is served by Nginx, which also reverse-proxies `/api` and `/health` to the FastAPI backend. In development the Vite dev server proxies API requests directly.

## Getting Started

The fastest way to get Chronicle running is with Docker — see [`docs/QUICK_START.md`](docs/QUICK_START.md).
```bash
git clone https://github.com/ImPhantom/chronicle.git
cd chronicle

docker compose up --build
# App will be accessible at http://localhost:8080 (by default)
```

If you wish to contribute, or even just run the project locally without docker — see [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend framework | Vue 3 + TypeScript |
| Frontend build | Vite + Bun |
| UI components | shadcn-vue (reka-ui) + Tailwind CSS v4 |
| Icons | Phosphor Icons |
| Utilities | vue-router |
| Backend framework | FastAPI (Python) |
| Database | SQLite via SQLAlchemy |
| Validation | Pydantic |
| Image capture | FFmpeg subprocess, OpenCV |
| Scheduling | APScheduler |
| Deployment | Docker + Nginx |
