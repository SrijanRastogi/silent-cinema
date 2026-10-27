#!/usr/bin/env python3
"""Validate the repository's Markdown and machine-readable configuration.

Checks:
- required documents exist,
- relative Markdown links resolve,
- project skills declare ``name`` and ``description`` front matter,
- no trailing whitespace in tracked text files,
- JSON files parse.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    "AGENTS.md",
    "API.md",
    "ARCHITECTURE.md",
    "BACKLOG.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "DATABASE.md",
    "DEPLOYMENT.md",
    "PLAN.md",
    "README.md",
    "SECURITY.md",
    "TESTING.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/STATUS.md",
    "docs/QUALITY_GATES.md",
    "docs/DECISIONS.md",
    "docs/UI.md",
]

SKIP_DIRS = {".git", ".venv", "node_modules", "dist", "coverage", "data", "__pycache__"}

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCE = re.compile(r"```.*?```", re.DOTALL)


def tracked_files(suffix: str) -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob(f"*{suffix}")
        if not any(part in SKIP_DIRS for part in path.parts)
    )


def check_links(path: Path, text: str) -> list[str]:
    problems: list[str] = []
    for raw in LINK.findall(FENCE.sub("", text)):
        target = raw.strip().split()[0].strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        file_part = target.split("#", 1)[0]
        if not file_part:
            continue
        resolved = (path.parent / file_part).resolve()
        if not resolved.exists():
            problems.append(f"{path.relative_to(ROOT)}: broken link -> {target}")
    return problems


def check_skill_frontmatter(path: Path, text: str) -> list[str]:
    if not text.startswith("---\n"):
        return [f"{path.relative_to(ROOT)}: missing front matter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return [f"{path.relative_to(ROOT)}: unterminated front matter"]
    block = text[4:end]
    missing = [key for key in ("name:", "description:") if key not in block]
    return [f"{path.relative_to(ROOT)}: missing {key}" for key in missing]


def main() -> int:
    problems: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            problems.append(f"missing required document: {relative}")

    for path in tracked_files(".md"):
        text = path.read_text(encoding="utf-8")
        problems.extend(check_links(path, text))
        for number, line in enumerate(text.splitlines(), start=1):
            if line != line.rstrip():
                problems.append(f"{path.relative_to(ROOT)}:{number}: trailing whitespace")

    for path in sorted((ROOT / ".opencode" / "skills").glob("*/SKILL.md")):
        problems.extend(check_skill_frontmatter(path, path.read_text(encoding="utf-8")))

    for path in tracked_files(".json"):
        if path.name == "package-lock.json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            problems.append(f"{path.relative_to(ROOT)}: invalid JSON ({error})")

    if problems:
        print(f"docs-check: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        f"docs-check: OK ({len(REQUIRED)} required documents, "
        f"{len(tracked_files('.md'))} Markdown files, skills and JSON validated)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
