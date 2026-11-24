# CapstoneRPi: Whyre 2D Imaging device app

A native PySide6 kiosk app for a clinical skin assessment device: a Raspberry
Pi with a CSI camera and a 1280×800 touch display (landscape). It implements
the screens from the Whyre Figma design, plus live camera capture, on-device
storage in SQLite, and kiosk mode.

## Run on a PC (development)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt          # Windows: .venv\Scripts\pip
.venv/bin/python -m skin_assessment.main --demo    # demo data, simulated camera
```

| Flag | Effect |
|------|--------|
| `--kiosk` | Fullscreen, frameless, hidden cursor |
| `--demo` | Uses `demo.db` next to the database, seeded with 4 sample sessions |
| `--camera auto\|pi\|sim` | `auto` uses the Pi camera on a Raspberry Pi and a simulated camera elsewhere |
| `--db PATH` | SQLite database file (default `~/skin_assessment_data/sessions.db`, or `$SKIN_ASSESSMENT_DB`) |

Without `--kiosk` the window is a fixed 1280×800. **Ctrl+D** toggles the
simulated clinical SSD connection; toggling it during an export triggers the
Export failed screen.

## Install on the Raspberry Pi

Raspberry Pi OS Bookworm (64-bit; PySide6 wheels are not available for 32-bit):

```bash
sudo apt update && sudo apt install -y python3-picamera2 python3-venv
rpicam-hello --list-cameras          # the camera must be listed here
git clone <repo> ~/CapstoneRPi && cd ~/CapstoneRPi
python3 -m venv --system-site-packages .venv   # lets the venv see picamera2
.venv/bin/pip install -r requirements.txt
./deploy/run-kiosk.sh                 # try it
```

Without `--system-site-packages` the venv cannot import Picamera2, and the
Capture screen shows that the camera is not available.

`run-kiosk.sh` runs the app with `--kiosk` on Wayland
(`QT_QPA_PLATFORM=wayland`, the default desktop on Bookworm). Set
`QT_QPA_PLATFORM=xcb` before running it to use X11 instead.

Camera notes:

- The Pi 5 uses the narrow 22-pin camera connectors (CAM/DISP 0 or 1). Older
  camera modules need a 22-to-15-pin cable.
- If no camera is detected, or Picamera2 cannot be loaded, the app says the
  camera is not available and gives the reason. On a Raspberry Pi it never
  falls back to a simulated camera unless forced with `--camera sim`.
- With autofocus cameras (e.g. Camera Module 3), continuous autofocus runs in
  the viewfinder and a focus cycle runs before each still. Stills are saved as
  JPEG at full sensor resolution (quality 95).

## Start on boot (kiosk)

Choose one of these:

- **labwc autostart** (recommended; default desktop on current Bookworm): add
  `/home/<user>/CapstoneRPi/deploy/run-kiosk.sh &` to `~/.config/labwc/autostart`.
- **systemd user service** (restarts the app if it exits): see the header of
  [deploy/skin-assessment.service](deploy/skin-assessment.service). It expects
  the repo at `~/CapstoneRPi`; edit `ExecStart` if it is elsewhere.

Also turn off screen blanking (`sudo raspi-config` → Display Options → Screen
Blanking → No) and set the desktop to auto-login, so the kiosk starts without
a keyboard.

There is intentionally no way to exit the app from the touchscreen. For
maintenance, connect over SSH (with the systemd service, run
`systemctl --user stop skin-assessment` first, because it restarts the app).

## Data on the device

```text
~/skin_assessment_data/
  sessions.db               SQLite database (sessions table)
  photos/SES-000001.jpg     the session's photo, written on Confirm & Save
  photos/pending.jpg        the current capture, until it is saved or discarded
```

The `sessions` table has `id`, `image_url`, `skin_type`, `erythema_grade`,
`saved_at` and `updated_at`. `id` generates the session ID, shown as
`SES-000123`. `image_url` is relative to the database folder. A session is
complete when it has a skin type, an erythema grade and a photo, and counts as
edited once `updated_at` is later than `saved_at`.

A capture is a draft: only Confirm & Save moves `pending.jpg` to the session's
photo and updates the database. Every other exit discards it, and a leftover
draft is deleted when the app starts. Retaking a photo while editing a session
replaces that session's photo when it is saved.

## Display

The app is sized for the 1280×800 touch display. The Figma frames are
1024×600; every Figma measurement goes through `theme.px()`, which scales it
by 1280/1024 (`SCREEN_WIDTH`/`SCREEN_HEIGHT` in
[skin_assessment/theme.py](skin_assessment/theme.py)). The display is
taller than the Figma frame, so the extra height goes to the content area
between the header and footer. Export data and Export failed were drawn for
800×480; `theme_legacy.lpx()` scales them by 1280/800.

## Screens

| Screen | File |
|--------|------|
| Home | `screens/home.py` |
| New session | `screens/new_session.py` |
| Skin type / Erythema grade | `screens/assessment.py` |
| Take photo | `screens/take_photo.py` |
| Confirm photo | `screens/confirm_photo.py` |
| Session saved | `screens/session_saved.py` |
| Past sessions | `screens/past_sessions.py` |
| Session detail | `screens/session_detail.py` |
| Export data | `screens/export_data.py` |
| Export complete | `screens/export_complete.py` |
| Export failed | `screens/export_failed.py` |

Export data and Export failed keep the original wireframe look
(`theme_legacy.py`).

## Architecture

All paths are under `skin_assessment/`.

- `main.py`: `MainWindow` hosts a `QStackedWidget` and is the navigation
  controller. It carries a draft session through the new-session and
  edit-session steps and saves it.
- `app_state.py`: the `Session` model, `SessionStore` (SQLite) and `AppState`
  (session queries, draft photo handling, SSD status).
- `camera.py`: `PiCamera` (Picamera2: preview thread and full-resolution
  still), `SimulatedCamera` and `UnavailableCamera`.
- `export.py`: `SimulatedExporter` (see below).
- `theme.py`: colours, Inter type sizes, layout constants and the stylesheet.
  Inter is bundled in `assets/fonts` (SIL OFL).
- `widgets.py`: shared components (header, buttons, option selectors,
  image previews).
- `screens/`: one module per screen.

## Not yet implemented

- SSD detection and export file writing. `SimulatedExporter` walks the
  selected records and honours the simulated SSD connection (Ctrl+D), so the
  connected, exporting, complete and failed states can all be exercised.
