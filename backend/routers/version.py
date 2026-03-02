import os
import subprocess

from fastapi import APIRouter

router = APIRouter()

def _resolve_git_hash() -> tuple[str, str]:
    """Return (short_hash, full_hash). Checks GIT_HASH env var first, then git subprocess."""
    full = os.getenv("GIT_HASH", "").strip()
    if not full or full == "unknown":
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                full = result.stdout.strip()
        except Exception:
            pass
    if not full:
        full = "unknown"
    short = full[:7] if full != "unknown" else "unknown"
    return short, full

_GIT_HASH, _GIT_HASH_FULL = _resolve_git_hash()


@router.get("/version")
def get_version():
    return {"git_hash": _GIT_HASH, "git_hash_full": _GIT_HASH_FULL}
