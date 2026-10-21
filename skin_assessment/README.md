# Skin Assessment — PySide6 Frontend

A low-fidelity front-end prototype for a clinical skin assessment workflow,
built with PySide6 and sized for a 7-inch Raspberry Pi touchscreen
(800×480, landscape). It implements all screens from the Figma wireframe.

## Run

```bash
.venv/bin/python -m skin_assessment.main
```

## Screens (mapped to the wireframe)

| Screen                 | Wireframe page | File                              |
|------------------------|----------------|-----------------------------------|
| Home                   | 5              | `screens/home.py`                 |
| Patient assessment     | 1              | `screens/assessment.py`           |
| Take photo             | 2              | `screens/take_photo.py`           |
| Confirm photo          | 3              | `screens/confirm_photo.py`        |
| Session saved          | 4              | `screens/session_saved.py`        |
| Past sessions          | 6              | `screens/past_sessions.py`        |
| Session detail         | 7              | `screens/session_detail.py`       |
| Export data            | 8 & 10         | `screens/export_data.py`          |
| Export complete        | 9              | `screens/export_complete.py`      |
| Export failed          | 11             | `screens/export_failed.py`        |

## Architecture

- `main.py` — `MainWindow` hosts a `QStackedWidget`. It acts as the navigation
  controller: screens call methods like `show_take_photo()` / `go_home()`.
- `app_state.py` — `AppState` + `Session` dataclass. Sessions live in memory and
  are seeded with the four sample sessions from the wireframe.
- `theme.py` — shared QSS stylesheet and the 800×480 size constants.
- `widgets.py` — reusable `Header`, `OptionButton` (toggle), `ImagePlaceholder`
  (crossed grey box), and a `make_button(variant=...)` helper.

## Demoing SSD states

Press **Ctrl+D** to toggle the Clinical SSD between connected and not-connected.
This drives the Export screen's connected (page 8) vs not-connected (page 10)
states and enables/disables the export button. The Export failed screen
(page 11) is reachable via `show_export_failed()`.

## Integration points (left as stubs for the capstone backend)

- Camera capture in `take_photo.py` (`_capture`) just flips a `has_photo` flag.
- `save_draft()` in `main.py` stamps a save time and keeps the session in memory;
  wire this to real persistence.
- Export actions navigate to the result screens without writing files.
