"""Safe subprocess execution for FFmpeg and Tesseract."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence


class MediaProcessError(RuntimeError):
    """An external media tool failed or could not be started."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def run_tool(
    argv: Sequence[str],
    *,
    timeout_seconds: float,
    stdin_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run an external tool with argv only, no shell, a timeout, and captured output."""
    try:
        return subprocess.run(
            list(argv),
            input=stdin_bytes,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
    except FileNotFoundError as error:
        raise MediaProcessError(
            "tool_missing", f"The media tool '{argv[0]}' is not installed or not on PATH."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise MediaProcessError(
            "tool_timeout", f"The media tool '{argv[0]}' exceeded its time limit."
        ) from error


def stderr_summary(result: subprocess.CompletedProcess[bytes], limit: int = 300) -> str:
    """Return a short single-line stderr summary without dumping the whole log."""
    text = result.stderr.decode("utf-8", errors="replace").strip()
    if not text:
        return "no diagnostic output"
    last_line = text.splitlines()[-1].strip()
    return last_line[:limit]
