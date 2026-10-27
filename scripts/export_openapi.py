"""Export the FastAPI OpenAPI schema for frontend type generation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://silent:silent_dev@127.0.0.1:5432/silent_cinema",
)

from silent_cinema.app import app  # noqa: E402


def main() -> int:
    destination = ROOT / "apps" / "web" / "src" / "api" / "openapi.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    destination.write_text(
        json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {destination.relative_to(ROOT)} ({len(schema.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
