# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chronicle is a timelapse management app for network cameras. It captures RTSP streams as WebP images via FFmpeg, stores metadata in SQLite, and presents a management UI.

## Architecture

```
chronicle/
├── backend/        # Python + FastAPI
└── frontend/       # Vite + Vue 3 + TypeScript
```

### Backend (Python + FastAPI)

- **FastAPI** — HTTP API server
- **APScheduler** — schedules periodic camera capture jobs
- **SQLAlchemy + SQLite** — persistent storage for cameras and timelapse metadata
- **FFmpeg** subprocess — captures RTSP streams to WebP images
- Entry point: `backend/main.py`
- Dependencies: `backend/requirements.txt`

### Frontend (Vite + Vue 3)

- **Vue 3** with TypeScript
- **shadcn-vue + Tailwind** — UI components and styling (planned; not yet installed)
- **vue-router** — client-side routing (planned; not yet installed)
- **Pinia** — state management (planned; not yet installed)
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
