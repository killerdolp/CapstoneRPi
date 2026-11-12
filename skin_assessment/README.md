# Skin Assessment: PySide6 device app

A native kiosk app for a clinical skin assessment device: a Raspberry Pi 5
with a CSI camera and the official 7" Raspberry Pi Touch Display (800×480,
landscape). It implements every screen from the Figma wireframe, plus live
camera capture, on-device storage, and kiosk mode.

## Run on a PC (development)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip
.venv/bin/python -m skin_assessment.main --demo  # demo data, simulated camera
```

| Flag | Effect |
|---|---|
| `--kiosk` | Fullscreen, frameless, hidden cursor |
| `--demo` | Uses `<data-dir>/demo` with labelled demonstration sessions. The header shows **DEMO DATA** |
| `--camera auto\|pi\|sim` | `auto` picks the Pi camera when Picamera2 is installed, otherwise a simulated camera |
| `--data-dir PATH` | Where sessions are stored (default `~/skin_assessment_data`, or `$SKIN_ASSESSMENT_DATA`) |

**Ctrl+D** toggles the simulated clinical SSD connection. Toggling it during an
export triggers the *Export failed* state. Set `SKIN_REDUCED_MOTION=1` to
turn off the label print animation.

## Install on the Raspberry Pi 5

Raspberry Pi OS Bookworm (64-bit):

```bash
sudo apt update && sudo apt install -y python3-picamera2 python3-venv
rpicam-hello --list-cameras          # the camera must be listed here
git clone <repo> ~/CapstoneRPi && cd ~/CapstoneRPi
python3 -m venv --system-site-packages .venv   # lets the venv see picamera2
.venv/bin/pip install -r requirements.txt
./deploy/run-kiosk.sh                 # try it
```

Camera notes:
- The Pi 5 uses the narrow 22-pin camera connectors (CAM/DISP 0 or 1). Older
  camera modules need a 22-to-15-pin cable.
- If `rpicam-hello --list-cameras` shows nothing, the app shows *Camera not
  available* and lets the user save sessions as incomplete. It never falls
  back to a simulated camera on the device.
- With Camera Module 3, continuous autofocus runs in the viewfinder, and a
  focus cycle runs before each still. Stills are saved as JPEG at full sensor
  resolution (quality 95).

### Start on boot (kiosk)

Choose **one** of these:

- **labwc autostart** (default desktop on current Bookworm): add
  `/home/<user>/CapstoneRPi/deploy/run-kiosk.sh &` to `~/.config/labwc/autostart`.
- **systemd user service** (restarts the app if it exits): see the header of
  `deploy/skin-assessment.service`.

Also turn off screen blanking (`sudo raspi-config` → Display Options → Screen
Blanking → No). Set the desktop to auto-login so the kiosk starts without a
keyboard.

## Data on the device

```
~/skin_assessment_data/
  sessions/S-0001.json     one record per session, written atomically (fsync + rename)
  photos/S-0001_r2.jpg     one photo per saved revision; older photos are never deleted
  pending/capture.jpg      the last capture, kept until it is confirmed or retaken
```

Each save creates a new `revision`. *Edit session* works on a copy, so leaving
the edit without saving leaves the stored record unchanged.

## Design

The visual system is *Specimen Label*: each record looks like a clinical label
printed in thermal black on die-cut stock. A session's state is always shown by
line style as well as colour:

| Edge | Meaning |
|---|---|
| Solid | Complete |
| Perforated (dashed) | Incomplete |
| Hatched | Unavailable (disabled action, missing photo, no camera/SSD) |
| STAT orange flag | Needs attention; always carries a text label |

Type is Atkinson Hyperlegible Next and Mono (SIL OFL, bundled in
`assets/fonts`). It uses four fixed sizes: 14, 17, 23 and 36 px. Touch targets
are at least 48 px, and primary actions are 60 px. Tokens live in `theme.py`.

## Architecture

- `main.py`: `MainWindow` is the navigation controller and runs the session
  workflow (draft copy, pending photo, discard confirmation, save).
- `app_state.py`: the `Session` model, `SessionStore` (JSON + JPEG
  persistence) and `AppState` (session list, SSD status, `changed` signal).
- `camera.py`: `PiCamera` (Picamera2: preview thread + full-res still),
  `SimulatedCamera`, and `UnavailableCamera`.
- `export.py`: `SimulatedExporter` (see *Not yet implemented*).
- `widgets.py`: the painted component set (label cards, buttons, grade
  selector, viewfinder, Code 128 barcode, running head, print feed,
  confirmation sheet).
- `screens/`: one module per wireframe screen.

## Not yet implemented

- **SSD export.** There is no USB SSD detection, and no files are written yet.
  `export.SimulatedExporter._write_record` is the integration point. SSD state
  is simulated with Ctrl+D.
- **Schema version.** `SCHEMA_VERSION` in `app_state.py` is provisional (`1.0`).
- **Colour calibration.** There is no white-balance lock or colour reference
  workflow yet. Clinical photography will probably need fixed AWB/exposure
  settings.
