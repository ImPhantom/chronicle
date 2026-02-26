# Quick Start — Docker

By far the easiest way to get the project up and running, a simple `docker compose up` command runs the backend API in a slim python container and serves the built frontend via an Nginx container.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (v2+)
- FFmpeg available on the host is **NOT** required — it is bundled in the container

## 1. Clone the repository

```bash
git clone https://github.com/ImPhantom/chronicle.git
cd chronicle
```

## 2. (Optional) Configuration

The defaults should work fine out of the box for a local installation.

If you want/need to customise anything, edit `docker-compose.yml` and adjust the `environment` block under the `backend` service:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:////app/data/chronicle.db` | SQLite connection string |
| `STORAGE_PATH` | `/app/data` | Root directory for captured frames and exports |
| `CORS_ORIGINS` | `http://localhost` | Allowed CORS origin(s) |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

Captured frames and the database are written to `./data/` in the project root (mounted into the container). This directory is created automatically on first run.

If you need to change the port (default `:8080`), edit the following value in `docker-compose.yml`:
```yaml
services:
  nginx:
    ports:
      - "8080:80" # Change the left side to your preferred host port
```

## 3. Build and start

```bash
docker compose up --build
```

The first build takes a few minutes while it installs Python and Node dependencies and compiles the frontend. Subsequent starts are fast.

Once running, open **http://localhost:8080** in your browser. (if you changed the port, be sure you're using it when trying to access the site.)

If you cant access the frontend, check the container status:
```bash
# list containers & their status
docker compose ps

# check for errors in logs
docker compose logs
```

## 4. Stopping

```bash
docker compose down
```

Your data in `./data/` is preserved. To also wipe the database and all captured frames:
