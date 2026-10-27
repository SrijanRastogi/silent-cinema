# UI.md — Design Direction and System

Status: **M1 shell built; review editor and export screens are planned.** The
current UI contains the app shell, honest empty dashboard, system status, and
404 pages only.

## 1. Product character

An **archival workstation**, not an admin dashboard. The user is doing careful,
frame-accurate editorial work on a film print. The interface should feel like a
well-made editing bench: calm, precise, warm, and legible for long sessions.

Avoid:

- generic SaaS dashboard layouts with invented KPIs,
- purple/blue gradient "AI product" styling,
- glassmorphism, neon, heavy shadows,
- decorative animation that competes with video playback,
- fake charts, fake counts, or sample data presented as real.

## 2. Visual language

### Typography

| Role | Family | Use |
|---|---|---|
| Display / headings | **Newsreader** (serif, self-hosted via Fontsource) | Page titles, film titles, section headings |
| UI / body | **IBM Plex Sans** | Labels, buttons, body, tables |
| Timecode / technical | **IBM Plex Mono** | Timestamps, frame values, job IDs, SRT preview |

Rules:

- Headings are sentence case, not all caps.
- Timecodes are always monospace and aligned by colon.
- Body measure 60–75 characters.
- No more than three families.
- Fonts must be self-hosted; no runtime font CDN dependency.

### Colour

Warm neutral base with a film-amber accent. Both themes are first-class.

| Token | Dark | Light | Use |
|---|---|---|---|
| `--ink` | `#EDE6DA` | `#171411` | Primary text |
| `--surface` | `#14120F` | `#F6F1E8` | App background |
| `--panel` | `#1D1A16` | `#FFFDF8` | Cards, panels |
| `--line` | `#332E27` | `#DDD4C6` | Borders, dividers |
| `--muted` | `#9A9083` | `#6B6257` | Secondary text |
| `--amber` | `#D99A4E` | `#9A5B12` | Primary action, focus, active stage |
| `--verified` | `#6FA79B` | `#2F6B5F` | Reviewed/success |
| `--danger` | `#D8795F` | `#9E3B24` | Errors, destructive |
| `--warning` | `#D9B45E` | `#8A6414` | Unreviewed, degraded |

Rules:

- Body text contrast ≥ 4.5:1; large text ≥ 3:1.
- Amber is not used for large text on dark backgrounds without checking
  contrast.
- Status is never conveyed by colour alone; pair with icon and label.
- No gradients except a subtle film-grain/vignette texture on the dashboard
  header, disabled under `prefers-reduced-motion`/low-power if it costs
  performance.

## 3. Layout

- **App shell:** slim left rail (72 px collapsed / 232 px expanded), top
  context bar, content region max 1440 px.
- **Dashboard:** recent films as a list/table with real state, not cards full of
  fake metrics.
- **Upload:** single focused drop zone, file constraints visible, real progress.
- **Processing:** stage timeline with actual backend state, elapsed time, and
  cancel where allowed.
- **Review editor:** the centrepiece.
  - Desktop: video preview (top-left), entry table (bottom-left), inspector
    (right).
  - Laptop 1366×768: video 16:9 above a scrollable entry list; inspector
    collapses to a drawer.
  - Mobile: read-only review is acceptable; editing may be limited with a clear
    notice.
- **Export:** track validation summary, format choice, preview, downloads.

No horizontal scrolling at 1280 px.

## 4. Component system

- **shadcn/ui** is the base: buttons, inputs, dialogs, menus, tables, tabs,
  tooltips, toasts.
- **Watermelon UI** blocks may be used for dashboard/template composition. It is
  a shadcn registry (MIT), not an npm dependency.
  - Install only the specific block:
    `npx shadcn@latest add https://registry.watermelon.sh/r/<slug>.json`
  - Verify the generated code before committing.
  - Record the source URL and date in the component header and
    `THIRD_PARTY_NOTICES.md`.
  - Remove decorative animation from editing surfaces.
- Do not install the npm package `watermelon-ui`.
- Do not mix Base UI and Radix primitives without an ADR.
- Domain components (`TimecodeInput`, `EntryRow`, `JobStateBadge`,
  `ReviewStatus`) live in `apps/web/src/components/` and compose primitives.

## 5. Interaction rules

- Every async action has idle, pending, success, and error states.
- Progress reflects the backend; if unknown, show an indeterminate state
  labelled as such, never a fake percentage.
- Destructive actions require confirmation and name the object.
- Unsaved edits are visible; navigation warns before discarding.
- Timecode inputs accept `hh:mm:ss.mmm` and `mm:ss.mmm`, validate on blur, and
  show the normalized value.
- Overlap errors point to both entries involved.
- Machine-generated vs reviewed text is visually distinct but not colour-only.
- Keyboard: `Space` play/pause, `←/→` seek, `J/K/L` optional, `Enter` edit,
  `Esc` cancel, `Cmd/Ctrl+Enter` save.
- Focus is never trapped outside dialogs; focus returns to the trigger.

## 6. Page requirements

### Dashboard
- Real recent media and jobs.
- Clear upload CTA.
- Failed jobs visible with a safe reason and retry/cancel where supported.
- Empty state explains the workflow in one sentence.
- No invented statistics.

### Upload
- Drag-and-drop plus file picker.
- Allowed formats and size limit stated before selection.
- Client-side checks are convenience only; server errors are surfaced verbatim
  (safe messages).
- Real upload progress with cancel.

### Processing
- Job state, stage, elapsed time, and attempt count.
- Polling with backoff; stop on terminal state.
- Cancel button only when allowed.
- Explicit "worker not running" state if jobs stall (based on lease/status, not
  guesswork).

### Review editor
- Video preview with subtitle overlay.
- Entry list with timecodes, text, confidence, and review state.
- Edit, add, delete, reorder, jump-to-time.
- Validation blocks save/export on overlap or invalid duration.
- Clear distinction between OCR and human-edited text.

### Export
- Validation summary before export.
- SRT primary, WebVTT secondary.
- Preview of the first N cues with timecodes.
- Download buttons only for validated artifacts.
- Explanation that subtitles are not burned into the video.

## 7. Accessibility

Target WCAG 2.2 AA:

- Semantic landmarks and headings.
- Visible focus ring using `--amber`.
- All controls reachable and operable by keyboard.
- Labels tied to inputs; errors announced with `aria-live`.
- Video player controls accessible; captions/subtitles selectable.
- `prefers-reduced-motion` honoured; no autoplay animation.
- Colour is never the only status indicator.
- Touch targets ≥ 44 px where practical.

## 8. Content and tone

- Plain, specific language. "No worker is processing jobs" not "Something went
  wrong".
- Never claim OCR accuracy or language support in the UI beyond tested facts.
- When `stum` is enabled, show a persistent, dismissible-but-visible notice:
  "Optional stum detector · CC-BY-NC · non-commercial use only".
- Empty states suggest the next action.

## 9. Testing

- Component tests for timecode input, overlap validation, review status, and
  job state rendering.
- Visual check at 1280×720, 1366×768, and 1920×1080.
- Playwright covers upload → process → review → export.
- Accessibility: axe checks on primary pages; manual keyboard pass.

## 10. Open questions

- Whether the review editor should support waveform/audio (silent films often
  have music tracks); deferred.
- Whether light theme ships in v1 or ships dark-first with a light token set.
- Final font licensing and self-hosting strategy.
