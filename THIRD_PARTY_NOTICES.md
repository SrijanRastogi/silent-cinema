# THIRD_PARTY_NOTICES.md

This inventory is maintained as dependencies are adopted. An entry marked
**[UNVERIFIED]** must be confirmed with the actual installed artefact or
licence file before a release. Versions below are the pins in `uv.lock` and
`apps/web/package-lock.json` unless stated otherwise.

## 1. Project licence

The project is MIT licensed (`LICENSE`). Third-party components remain under
their own terms.

## 2. Components with verified terms

| Component | Version / source | Licence | Verification |
|---|---|---|---|
| `stum` | `Modern36/stum`, last push 2025-06-05 | **CC-BY-NC-4.0** | Read `LICENSE` and `pyproject.toml` in the official repository (2026-10-27) |
| Watermelon UI platform | `WatermelonCorp/watermelon-platform` | MIT | GitHub repository licence API (2026-10-27) |
| Watermelon UI registry | `WatermelonCorp/watermellon-registry` | MIT | GitHub repository licence API (2026-10-27) |
| shadcn/ui | `shadcn-ui/ui` | MIT | Official documentation and repository |
| React | npm latest 19.3.1 | MIT | npm registry metadata (2026-10-27) |
| Vite | npm latest 8.3.5 | MIT | npm registry metadata (2026-10-27) |
| Tailwind CSS | npm latest 4.3.3 | MIT | npm registry metadata (2026-10-27) |
| TypeScript | npm latest 7.0.2; project pins 5.9.3 | Apache-2.0 | npm registry metadata (2026-10-27) |
| TanStack Query | npm latest 5.105.0 | MIT | npm registry metadata (2026-10-27) |
| React Router DOM | npm latest 7.18.4 | MIT | npm registry metadata (2026-10-27) |
| Zod | npm latest 4.6.7 | MIT | npm registry metadata (2026-10-27) |
| React Hook Form | npm latest 7.91.0 | MIT | npm registry metadata (2026-10-27) |
| Vitest | npm latest 5.0.5 | MIT | npm registry metadata (2026-10-27) |
| Playwright Test | npm latest 1.64.1 | Apache-2.0 | npm registry metadata (2026-10-27) |
| OpenCV (Python headless) | PyPI 5.0.0.93 | Apache-2.0 | PyPI classifier (2026-10-27) |
| pytesseract | PyPI 0.3.13 | Apache-2.0 | PyPI classifier (2026-10-27) |
| NumPy | PyPI 2.5.4 | BSD-3-Clause | PyPI metadata (2026-10-27) |
| Pillow | PyPI 13.0.0 | HPND | PyPI metadata (2026-10-27) |
| `@tanstack/react-query` | npm 5.104.5 | MIT | npm registry metadata (2026-10-27) |
| `react-router-dom` | npm 7.18.4 | MIT | npm registry metadata (2026-10-27) |
| `lucide-react` | npm 1.61.0 | ISC | npm registry metadata (2026-10-27) |
| `class-variance-authority` | npm 0.7.1 | Apache-2.0 | npm registry metadata (2026-10-27) |
| `@radix-ui/react-slot` | npm 1.5.0 | MIT | npm registry metadata (2026-10-27) |
| `@fontsource/newsreader` | npm 5.3.0 | OFL-1.1 | npm registry metadata (2026-10-27) |
| `@fontsource/ibm-plex-sans` | npm 5.3.0 | OFL-1.1 | npm registry metadata (2026-10-27) |
| `@fontsource/ibm-plex-mono` | npm 5.3.0 | OFL-1.1 | npm registry metadata (2026-10-27) |
| `clsx`, `tailwind-merge` | npm 2.1.1, 3.7.0 | MIT | npm registry metadata (2026-10-27) |
| ESLint, Prettier, typescript-eslint, `@eslint/js` | npm pins in lockfile | MIT | npm registry metadata (2026-10-27) |
| Vitest, jsdom, Testing Library | npm pins in lockfile | MIT | npm registry metadata (2026-10-27) |
| `openapi-typescript`, `@vitejs/plugin-react`, `@tailwindcss/vite`, `globals` | npm pins in lockfile | MIT | npm registry metadata (2026-10-27) |

## 3. Planned dependencies — confirm at install

These are approved at the architecture level; the exact licence text and
version must be recorded by the M1 licence inventory before release.

| Component | Expected licence | Notes |
|---|---|---|
| FastAPI | MIT | Confirm from installed metadata |
| Pydantic | MIT | Confirm |
| SQLAlchemy | MIT | Confirm |
| Alembic | MIT | Confirm |
| psycopg 3 | LGPL-3.0 | Dynamic linking; confirm redistribution obligations |
| Uvicorn | BSD-3-Clause | Confirm |
| PostgreSQL | PostgreSQL License | Server dependency, not redistributed by us |
| Tesseract OCR | Apache-2.0 | System dependency; language packs have their own terms |
| FFmpeg | LGPL-2.1+ **or GPL** depending on build flags | See warning below |
| Ruff | MIT | Dev dependency |
| MyPy | MIT | Dev dependency |
| pytest | MIT | Dev dependency |

## 4. `stum` — CC-BY-NC-4.0

`stum` is a tool for detecting and transcribing intertitles, developed for
Swedish newsreels. It is licensed **Attribution-NonCommercial 4.0
International**, which is **not** an OSI-approved open-source licence and
prohibits use "primarily intended for or directed towards commercial advantage
or monetary compensation."

Project policy:

- `stum` is **not bundled, vendored, copied, or imported** as a library.
- It is an **optional external CLI adapter**, disabled by default
  (`STUM_ENABLED=false`).
- Enabling it requires a separate installation (`pipx install stum`) and
  triggers a clear non-commercial notice in the UI and documentation.
- No `stum` models, test data, or source code are redistributed.
- The adapter parses the SRT files that `stum` produces; output parsing is our
  code.
- Attribution is provided here and in the application's "About" surface.
- The project's MIT licence does not grant rights to `stum`.

`stum` requires FFmpeg, Tesseract, the Swedish Tesseract model, and the EAST
text-detection model. Operators install these themselves. Its test data is
private and its accuracy on non-Swedish material is unverified.

Repository: <https://github.com/Modern36/stum>
Licence: <https://creativecommons.org/licenses/by-nc/4.0/>

## 5. Watermelon UI

Watermelon UI is an MIT-licensed shadcn registry. We may copy individual
blocks/components into `apps/web` rather than depend on a package.

When a block is copied:

1. Keep the MIT licence notice in the repository's `LICENSES/` or this file.
2. Record the source URL and retrieval date in the component's header comment
   or `docs/UI.md`.
3. Do not import the unrelated npm package `watermelon-ui` (an old ISC package
   from 2018 that is not WatermelonCorp's).
4. Review the copied code for accessibility, dependencies, and fit before
   committing.

## 6. FFmpeg licensing warning

FFmpeg's licence depends on how the binary was compiled. Builds with
`--enable-gpl` (common in distributions and static builds) are GPL-2.0-or-later
and impose redistribution obligations on binaries we ship. Before distributing
a container image or binary:

```bash
ffmpeg -version   # inspect configuration flags
```

Record the result in this file. If we ship FFmpeg, prefer an LGPL build or
satisfy GPL obligations. We do not modify FFmpeg source.

## 7. Models and language data

- No OCR models are committed to this repository.
- Tesseract language packs are installed by the operator via the OS package
  manager; their licences are recorded by that distribution.
- The EAST model used by `stum` is downloaded by the operator, not
  redistributed.
- No training data or film footage is included.

## 8. Attribution in the application

The About/Settings surface will list:

- the project licence,
- `stum` (when enabled) with its CC-BY-NC terms,
- Watermelon UI and shadcn/ui credits for copied components,
- Tesseract and FFmpeg as processing dependencies.
