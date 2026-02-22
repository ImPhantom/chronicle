import subprocess

import cv2

_FORMAT_VCODEC = {"webp": "webp", "jpeg": "mjpeg", "png": "png"}
_FORMAT_MEDIA_TYPE = {"webp": "image/webp", "jpeg": "image/jpeg", "png": "image/png"}
_FORMAT_EXT = {"webp": "webp", "jpeg": "jpg", "png": "png"}


class CaptureError(RuntimeError):
    pass


def capture_network_bytes(
    rtsp_url: str,
    *,
    image_format: str,
    rtsp_transport: str,
    timeout_seconds: int,
) -> bytes:
    vcodec = _FORMAT_VCODEC.get(image_format, "webp")
    cmd = [
        "ffmpeg",
        "-rtsp_transport", rtsp_transport,
        "-i", rtsp_url,
        "-frames:v", "1",
        "-f", "image2pipe",
        "-vcodec", vcodec,
        "pipe:1",
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise CaptureError(f"FFmpeg timed out after {timeout_seconds}s") from exc
    except FileNotFoundError as exc:
        raise CaptureError("FFmpeg not found on this system") from exc
    if result.returncode != 0 or not result.stdout:
        raise CaptureError("FFmpeg failed to capture a frame")
    return result.stdout


def capture_hardware_bytes(device_index: int, *, image_format: str) -> bytes:
    ext = f".{_FORMAT_EXT.get(image_format, 'webp')}"
    cap = cv2.VideoCapture(device_index)  # pylint: disable=no-member
    try:
        if not cap.isOpened():
            raise CaptureError(f"Could not open hardware camera at index {device_index}")
        ok, frame = cap.read()
        if not ok or frame is None:
            raise CaptureError("Failed to read frame from hardware camera")
        encode_ok, buf = cv2.imencode(ext, frame)  # pylint: disable=no-member
        if not encode_ok:
            raise CaptureError(f"Failed to encode frame as {image_format}")
        return buf.tobytes()
    finally:
        cap.release()
