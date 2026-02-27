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
```bash
docker compose down -v
```

## Hardware Camera Support

When running in Docker, hardware camera discovery (`cv2-enumerate-cameras`) cannot access the host's video devices directly. You must pass them through to the container.

### Linux

**1. Find your video devices:**

```bash
ls -la /dev/video*
```

**2. Add to `docker-compose.yml`:**

```yaml
services:
  backend:
    # ... existing config ...
    devices:
      - /dev/video0:/dev/video0
      - /dev/video1:/dev/video1
    # Add video group to allow access without root
    group_add:
      - video
```

Add one entry per camera, mapping the host device to the same path inside the container.

### Windows

Windows doesn't expose video devices the same way. You could possibly get it working with a **Video4Linux (V4L2) loopback**/WSL Hack.

Running the app outside of docker will allow you to see hardware cameras, but you'll lack any of the stability/reliability that comes with the docker setup.

### Verifying Device Access

After restarting the container, test hardware capture from the UI or API:

```bash
curl http://localhost:8080/api/cameras/hardware
```

If devices are properly passed through, this returns a list of available cameras.

---

## Using a Remote Camera via RTSP (MediaMTX)

If your camera is attached to a low-power device (e.g. a Raspberry Pi or other SBC) that isn't suitable for running Chronicle, you can use [MediaMTX](https://github.com/bluenviron/mediamtx) to publish that camera as an RTSP stream. Chronicle then connects to it over the network like any other IP camera — offloading all scheduling, frame storage, and export work to the Chronicle host.

### 1. Install MediaMTX on the source device

Download the latest release for your platform from the [MediaMTX releases page](https://github.com/bluenviron/mediamtx/releases) and extract the archive.

### 2. Configure a camera source

Edit `mediamtx.yml` to define a path for your camera:

```yaml
paths:
  cam:
    source: device:///dev/video0  # USB camera on Linux
    # source: rpiCamera://        # Raspberry Pi camera module
```

### 3. Run MediaMTX

```bash
./mediamtx
```

By default, the RTSP stream is served at:

```
rtsp://<device-ip>:8554/cam
```

### 4. Add the stream to Chronicle

In the Chronicle UI, add a new **Network (RTSP)** camera and enter the stream URL:

```
rtsp://<device-ip>:8554/cam
```

Use the **Test Capture** button to verify the stream is reachable before saving.
