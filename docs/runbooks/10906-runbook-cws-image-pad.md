# 10906 - CWS / AMO Image Padding

## Purpose

Pad a source screenshot to a store-listing canvas size (e.g. Chrome Web Store 1280x800, AMO equivalents) without cropping. The source is scaled-to-fit while preserving aspect ratio, then centered on a brand-color background.

Used for screenshots whose natural aspect ratio doesn't match the store requirement and where cropping would remove important content (e.g. WSJ article + Aletheia overlay both load-bearing for the demo).

## When to use

- Preparing screenshots for Chrome Web Store or Firefox AMO listings
- Any time `screenshots/cws/cws-image-N-<slug>.png` or `screenshots/amo/...` needs to be produced from a source screenshot
- Reference: per memory `project-cws-screenshot-padding-procedure`, do NOT crop revenue-bearing UI (Buy buttons, ads, paywalls) from third-party content (`feedback-fair-use-preserve-revenue-elements`)

## Prerequisites

- Pillow installed (already in `pyproject.toml`: `pillow = "^12.2.0"`)
- Source image file accessible (typically a screenshot under `C:\Users\mcwiz\OneDrive\Pictures\Screenshots\` — read-only single-file access is OK; do not enumerate that directory)

## Usage

```bash
poetry run python tools/cws_image_pad.py \
    --input "<absolute path to source image>" \
    --output screenshots/cws/cws-image-N-<slug>.png
```

### Defaults

| Flag | Default | Purpose |
|---|---|---|
| `--width` | `1280` | CWS preferred canvas width |
| `--height` | `800` | CWS preferred canvas height |
| `--color` | `#3B82F6` | Aletheia brand blue (from `extensions/chrome/overlay.js:126`, `.aletheia-badge.neutral`) |

### Examples

CWS 1280x800 (default):
```bash
poetry run python tools/cws_image_pad.py \
    --input "C:/Users/mcwiz/OneDrive/Pictures/Screenshots/Screenshot.png" \
    --output screenshots/cws/cws-image-2-loaded-language.png
```

CWS small thumbnail 640x400:
```bash
poetry run python tools/cws_image_pad.py \
    --input "..." \
    --output screenshots/cws/cws-image-N-small-<slug>.png \
    --width 640 --height 400
```

AMO different aspect ratio:
```bash
poetry run python tools/cws_image_pad.py \
    --input "..." \
    --output screenshots/amo/amo-image-N-<slug>.png \
    --width 1200 --height 800
```

## Output convention

| Target | Path |
|---|---|
| Chrome Web Store | `screenshots/cws/cws-image-N-<slug>.png` |
| Firefox AMO | `screenshots/amo/amo-image-N-<slug>.png` |

`N` is the slot number (1-4 on CWS). `<slug>` is a short content identifier (e.g. `epocha`, `loaded-language`, `popup-auth`).

## Return path format

When telling the operator the output path, return a clickable markdown link (per memory `feedback-clickable-paths`):

```
[cws-image-N-slug.png](file:///C:/Users/mcwiz/Projects/Aletheia/screenshots/cws/cws-image-N-slug.png)
```

Bare Windows paths don't auto-link in Claude Code.

## Upload procedure

After producing the asset:

1. Open the `cto@thrivetech.ai` Chrome profile
2. Click the first bookmark (CWS developer console)
3. Authenticate (Chrome saved password + Google Authenticator 2FA)
4. Aletheia item → Store listing → Graphic assets → Screenshots
5. Upload to the appropriate slot → Save draft → Submit for review (or Publish)
6. Verify on the public listing in incognito before closing any tracking issue

Reference: memory `user-cws-dashboard-access` for the access pattern.

## Verification

After running the tool:

- Confirm output file exists at the path printed
- Open and visually inspect:
  - Source content preserved (no cropping)
  - Brand color padding on sides or top/bottom (depending on source aspect)
  - Canvas size matches `--width` × `--height`

## Related

- Tool source: `tools/cws_image_pad.py`
- Issue origin: #635 (CWS screenshot replacement)
- Runbooks: `10905-runbook-cws-publish.md` (Chrome) and `10907-runbook-amo-publish.md` (Firefox) — the publishing flows this slots into
- Memory: `project_cws_screenshot_padding_procedure.md`
