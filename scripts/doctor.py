"""Environment doctor: report versions and missing prerequisites honestly."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


def load_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    env_file = ROOT / ".env"
    if not env_file.exists():
        return values
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


ENV_FILE = load_env_file()


def setting(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name) or ENV_FILE.get(name) or default


def run(
    command: list[str], timeout: int = 10, env: dict[str, str] | None = None
) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return completed.returncode, output.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


class Report:
    def __init__(self) -> None:
        self.ok = 0
        self.warnings = 0
        self.missing = 0

    def line(self, status: str, name: str, detail: str) -> None:
        print(f"[{status:<7}] {name:<18} {detail}")
        if status == "ok":
            self.ok += 1
        elif status == "warn":
            self.warnings += 1
        else:
            self.missing += 1


def first_line(text: str) -> str:
    return text.splitlines()[0] if text.splitlines() else "unknown"


def main() -> int:
    print("Silent Cinema — environment doctor")
    print(f"Repository: {ROOT}")
    print("")

    report = Report()

    if sys.version_info[:2] == (3, 13):
        report.line("ok", "Python", sys.version.split()[0])
    else:
        report.line("missing", "Python", f"{sys.version.split()[0]} (requires 3.13)")

    for name, command, check in [
        ("uv", ["uv", "--version"], None),
        ("node", ["node", "--version"], "24"),
        ("npm", ["npm", "--version"], None),
        ("ffmpeg", ["ffmpeg", "-version"], "8"),
        ("ffprobe", ["ffprobe", "-version"], "8"),
        ("tesseract", ["tesseract", "--version"], "5"),
        ("psql", ["psql", "--version"], "18"),
    ]:
        binary = shutil.which(command[0])
        if binary is None:
            report.line("missing", name, "not found on PATH")
            continue
        code, output = run(command)
        if code != 0:
            report.line("missing", name, f"could not run: {first_line(output)}")
            continue
        version_line = first_line(output)
        if check is not None and not re.search(rf"\b{re.escape(check)}[.\s]", version_line):
            report.line("warn", name, f"{version_line} (expected major {check})")
        else:
            report.line("ok", name, version_line)

    docker = shutil.which("docker")
    if docker is None:
        report.line("warn", "docker", "not installed (optional for M1)")
    else:
        code, output = run(["docker", "info", "--format", "{{.ServerVersion}}"])
        if code == 0:
            report.line("ok", "docker", f"daemon {output}")
            code, compose = run(["docker", "compose", "version"])
            if code == 0:
                report.line("ok", "docker compose", first_line(compose))
            else:
                report.line("warn", "docker compose", first_line(compose))
        else:
            report.line(
                "warn", "docker", "installed; daemon not reachable (re-login to docker group)"
            )

    code, languages = run(["tesseract", "--list-langs"])
    if code == 0:
        installed = {
            line.strip()
            for line in languages.splitlines()
            if line.strip() and not line.startswith("List of available")
        }
        if "eng" in installed:
            report.line("ok", "tesseract langs", ", ".join(sorted(installed)))
        else:
            report.line("missing", "tesseract langs", "eng not installed")

    database_url = setting("DATABASE_URL")
    if not database_url:
        report.line("missing", "database", "DATABASE_URL is not set")
    else:
        parsed = urlparse(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
        host = parsed.hostname or "127.0.0.1"
        port = str(parsed.port or 5432)
        user = unquote(parsed.username or "")
        database = (parsed.path or "/").lstrip("/")
        env = dict(os.environ)
        if parsed.password:
            env["PGPASSWORD"] = unquote(parsed.password)
        code, output = run(
            [
                "psql",
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                database,
                "-tAc",
                "select 1",
            ],
            timeout=10,
            env=env,
        )
        if code == 0 and output.strip() == "1":
            report.line("ok", "database", f"connected to {database} at {host}:{port}")
        else:
            report.line(
                "missing",
                "database",
                f"cannot connect to {database} at {host}:{port} ({first_line(output)})",
            )

    for label, path in [
        ("pyproject", "pyproject.toml"),
        ("uv lock", "uv.lock"),
        ("alembic", "alembic.ini"),
        ("API package", "apps/api/silent_cinema/app.py"),
        ("web package", "apps/web/package.json"),
        ("compose", "docker-compose.yml"),
    ]:
        if (ROOT / path).exists():
            report.line("ok", label, path)
        else:
            report.line("missing", label, path)

    print("")
    print(f"Result: {report.ok} ok, {report.warnings} warning(s), {report.missing} missing")
    print("Note: Playwright browsers are not required for M1 and are not checked here.")
    return 0 if report.missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
