# Contributing to Chronicle

Below is everything you need to get your development environment running and submit a good pull request.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Issues](#reporting-issues)

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Bun** — [bun.sh](https://bun.sh)
- **FFmpeg** — available on your `PATH`
- **Docker** (optional, for testing the production build locally)

### Backend

```bash
cd backend

pip install -r requirements.txt
uvicorn main:app --reload   # Starts on http://localhost:8000
```

### Frontend

```bash
cd frontend

bun install
bun run dev   # Starts on http://localhost:5173
```

The Vite dev server proxies `/api` and `/health` requests to the backend automatically — no extra configuration needed.

---

## Project Structure

```
chronicle/
├── backend/
│   ├── routers/    # FastAPI route handlers
│   ├── schemas/    # Pydantic request/response schemas
│   └── models/     # SQLAlchemy ORM models
└── frontend/
    └── src/
        ├── components/   # Vue components
        ├── views/        # Page-level components (vue-router)
        └── lib/          # Shared utilities and API client
```

---

## Development Workflow

### Branching

- Branch off `master` for all changes
- Use a short, descriptive branch name: `fix/rtsp-timeout`, `feat/camera-grid`, `docs/contributing`

### Commit Style

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add pause button to timelapse card
fix: prevent duplicate capture jobs on restart
docs: update quick start guide
style: align storage overview table columns
refactor: extract ffmpeg helpers into separate module
chore: bump reka-ui to 2.1.0
```

### Code Style

**Backend:**
- Follow existing patterns — routers stay thin, business logic lives in service functions
- Keep Pydantic schemas in `schemas/` and ORM models in `models/`

**Frontend:**
- Vue 3 Composition API (`<script setup>`) throughout — no Options API
- Tailwind CSS v4 for styling; use shadcn-vue components where possible
- Keep components focused — if a component is getting large, split it

---

### Testing the Docker build locally

CI publishes pre-built images to GHCR on every push to `master`, so the default `docker-compose.yml` pulls those. To test the Docker build from your local source, use the build override file:

```bash
# Build and start both containers from local source (GIT_HASH will show as "unknown")
docker compose -f docker-compose.yml -f docker-compose.build.yml up --build
```

To also bake in the real commit hash (useful for testing the version footnote):

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build --build-arg GIT_HASH=$(git rev-parse HEAD)
docker compose -f docker-compose.yml -f docker-compose.build.yml up
```

> **Note:** The `$(git rev-parse HEAD)` substitution requires a Unix shell (bash/zsh). On Windows, run this from Git Bash or WSL.

---

## Submitting a Pull Request

1. Fork the repo and create a branch from `master`
2. Make your changes and verify they work end-to-end
3. Test both the dev setup and, for significant changes, the Docker build
4. Open a PR with a clear title and description:
   - **What** changed and **why**
   - Any relevant screenshots or recordings for UI changes
   - Notes on anything that might need review

Pull requests should be focused — one feature or fix per PR where possible. Large, unrelated changes are harder to review and slower to merge.

---

## Reporting Issues

When filing a bug report, please include:

- A clear description of the problem and steps to reproduce it
- What you expected to happen vs. what actually happened
- Your setup: OS, Docker version (if applicable), camera type (RTSP/USB)
- Relevant logs from `docker compose logs` or the terminal output

Feature requests are welcome too — open an issue describing the use case and why it would be a good fit for Chronicle.
