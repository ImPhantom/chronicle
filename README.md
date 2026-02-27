# Chronicle
Timelapse management for network and hardware cameras.

## Overview

A simple self-hosted app for creating timelapses from IP cameras and USB webcams. It captures frames on a schedule, storing each as a WebP image. A web UI lets you browse and manage timelapses, preview the latest capture, control capture state, and export frames into a downloadable MP4 or WebM via FFmpeg.

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

## Requirements

> [!CAUTION]
> **Do not run Chronicle on a low-power SBC (e.g. Raspberry Pi).** Frame capture and video export via FFmpeg are CPU-intensive. Run Chronicle on a reasonably powerful machine or homelab server instead, and use a tool like [MediaMTX](https://github.com/bluenviron/mediamtx) on the SBC to expose its camera as an RTSP stream that Chronicle can pull from remotely.

### Host machine (running Chronicle)
- **CPU:** 4+ core/thread, modern mid-range or better
- **RAM:** 4–8 GB *(higher end recommended for large exports)*
- **Storage:** 30–100 GB, SSD preferred *(varies heavily by timelapse configuration and export frequency)*
- **Docker** with Compose plugin v2+

### Camera
- A hardware camera connected directly to the Docker host *(requires device passthrough — see [Quick Start](docs/QUICK_START.md))*
- A network camera accessible via RTSP *(IP cameras, or an SBC running MediaMTX)*

## Getting Started

```bash
git clone https://github.com/ImPhantom/chronicle.git
cd chronicle
docker compose up --build
# App accessible at http://localhost:8080 by default
```

For full setup instructions including configuration, hardware camera passthrough, and using MediaMTX to relay a remote camera — see [`docs/QUICK_START.md`](docs/QUICK_START.md).

To contribute or run the project locally without Docker — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

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
