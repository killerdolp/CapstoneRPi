"""Camera backends.

* ``PiCamera`` drives a CSI camera on the Raspberry Pi 5 camera connector via
  Picamera2/libcamera: a low-resolution preview stream for the viewfinder
  and a full-sensor-resolution still for the record.
* ``SimulatedCamera`` renders a synthetic scene so the app can be developed
  and demonstrated on a PC. The UI marks it SIMULATED everywhere.
* ``UnavailableCamera`` is used on the Pi when no camera is detected, so the
  UI can say so plainly instead of pretending.

Picamera2 is installed from apt on Raspberry Pi OS (``python3-picamera2``);
create the virtualenv with ``--system-site-packages`` so it is importable.
"""

from __future__ import annotations

import math
import queue
import random
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QRadialGradient,
)


class CameraState(Enum):
    LIVE = "live"
    SIMULATED = "simulated"
    UNAVAILABLE = "unavailable"


class CameraBackend(QObject):
    frame_ready = Signal(QImage)
    capture_finished = Signal(str)   # path of the written JPEG
    capture_failed = Signal(str)     # human-readable reason

    state: CameraState = CameraState.UNAVAILABLE
    description: str = ""
    still_size: Tuple[int, int] = (0, 0)
    error: str = ""

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def capture(self, path: Path) -> None: ...
    def shutdown(self) -> None:
        self.stop()


# ---------------------------------------------------------------------------
class UnavailableCamera(CameraBackend):
    def __init__(self, reason: str) -> None:
        super().__init__()
        self.state = CameraState.UNAVAILABLE
        self.description = "No camera detected"
        self.error = reason

    def capture(self, path: Path) -> None:
        self.capture_failed.emit(self.error or "Camera not available")


# ---------------------------------------------------------------------------
class SimulatedCamera(CameraBackend):
    """Synthetic forearm-like scene with a grey reference wedge."""

    PREVIEW = (640, 480)
    STILL = (2028, 1520)

    def __init__(self) -> None:
        super().__init__()
        self.state = CameraState.SIMULATED
        self.description = "Simulated camera (development only)"
        self.still_size = self.STILL
        self._t0 = time.monotonic()
        self._timer = QTimer(self)
        self._timer.setInterval(66)  # ~15 fps is plenty for a viewfinder
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        t = time.monotonic() - self._t0
        self.frame_ready.emit(render_scene(*self.PREVIEW, t))

    def capture(self, path: Path) -> None:
        t = time.monotonic() - self._t0

        def finish() -> None:
            image = render_scene(*self.STILL, t)
            if image.save(str(path), "JPG", 95):
                self.capture_finished.emit(str(path))
            else:
                self.capture_failed.emit("Could not write the photo to storage.")

        # Mimic the still-mode switch latency of the real sensor.
        QTimer.singleShot(450, finish)


def render_scene(w: int, h: int, t: float = 0.0, seed: int = 7) -> QImage:
    """Paint a synthetic skin patch: warm gradient, an erythematous area,
    a grey step wedge (like a photo reference card) and gentle hand shake."""
    img = QImage(w, h, QImage.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    s = w / 640.0
    dx = math.sin(t * 1.3) * 3 * s
    dy = math.cos(t * 0.9) * 2 * s

    base = QLinearGradient(0, 0, w, h)
    base.setColorAt(0.0, QColor("#d7a487"))
    base.setColorAt(0.55, QColor("#c98f71"))
    base.setColorAt(1.0, QColor("#b77c60"))
    p.fillRect(img.rect(), base)

    rng = random.Random(seed)
    p.setPen(Qt.NoPen)
    for _ in range(140):
        x, y = rng.random() * w, rng.random() * h
        r = (2 + rng.random() * 9) * s
        c = QColor(120, 70, 50, rng.randint(6, 18))
        p.setBrush(c)
        p.drawEllipse(QPointF(x + dx, y + dy), r, r)

    centre = QPointF(w * 0.46 + dx, h * 0.52 + dy)
    red = QRadialGradient(centre, w * 0.22)
    red.setColorAt(0.0, QColor(196, 70, 62, 200))
    red.setColorAt(0.6, QColor(200, 92, 76, 110))
    red.setColorAt(1.0, QColor(200, 110, 90, 0))
    p.setBrush(red)
    p.drawEllipse(centre, w * 0.24, h * 0.27)

    # Grey step wedge, as on a clinical photo reference card.
    steps = 6
    cw, ch = 34 * s, 24 * s
    x0, y0 = w - cw - 18 * s + dx, 18 * s + dy
    p.fillRect(QRectF(x0 - 4 * s, y0 - 4 * s, cw + 8 * s, ch * steps + 8 * s), QColor("#f4f4f2"))
    for i in range(steps):
        v = int(245 - i * 44)
        p.fillRect(QRectF(x0, y0 + i * ch, cw, ch), QColor(v, v, v))
    p.end()
    return img


# ---------------------------------------------------------------------------
class PiCamera(CameraBackend):
    """Picamera2 backend. Preview and capture run on one worker thread so
    libcamera calls are never issued concurrently."""

    def __init__(self, picam2, controls_module) -> None:
        super().__init__()
        self.state = CameraState.LIVE
        self._picam2 = picam2
        self._controls = controls_module
        props = picam2.camera_properties
        model = props.get("Model", "CSI camera")
        sensor_w, sensor_h = picam2.sensor_resolution
        self.still_size = (sensor_w, sensor_h)
        self._has_af = "AfMode" in picam2.camera_controls
        self.description = f"{model.upper()} · {sensor_w}×{sensor_h}" + (
            " · AF" if self._has_af else ""
        )

        # Viewfinder stream: ~960px wide at the sensor's aspect ratio.
        pw = 960
        ph = int(round(pw * sensor_h / sensor_w / 2) * 2)
        self._preview_cfg = picam2.create_preview_configuration(
            main={"size": (pw, ph), "format": "XRGB8888"}, buffer_count=4
        )
        self._still_cfg = picam2.create_still_configuration(
            main={"size": (sensor_w, sensor_h)}
        )
        picam2.options["quality"] = 95
        picam2.configure(self._preview_cfg)

        self._requests: "queue.Queue[Path]" = queue.Queue()
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        self._thread = threading.Thread(target=self._loop, name="camera", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None

    def capture(self, path: Path) -> None:
        self._requests.put(Path(path))
        if not self._running.is_set():
            self.start()

    def shutdown(self) -> None:
        self.stop()
        try:
            self._picam2.close()
        except Exception:  # pragma: no cover - hardware teardown
            pass

    # ---- worker thread -----------------------------------------------------
    def _loop(self) -> None:
        cam = self._picam2
        try:
            cam.start()
            if self._has_af:
                cam.set_controls({"AfMode": self._controls.AfModeEnum.Continuous})
        except Exception as exc:  # pragma: no cover - hardware
            self.capture_failed.emit(f"Camera failed to start: {exc}")
            self._running.clear()
            return

        while self._running.is_set():
            try:
                path = self._requests.get_nowait()
            except queue.Empty:
                path = None

            if path is not None:
                self._do_capture(path)
                continue

            try:
                frame = cam.capture_array("main")
            except Exception:  # pragma: no cover - hardware
                time.sleep(0.05)
                continue
            h, w = frame.shape[:2]
            image = QImage(frame.data, w, h, frame.strides[0], QImage.Format_RGB32).copy()
            self.frame_ready.emit(image)

        try:
            cam.stop()
        except Exception:  # pragma: no cover
            pass

    def _do_capture(self, path: Path) -> None:
        cam = self._picam2
        try:
            if self._has_af:
                cam.set_controls({"AfMode": self._controls.AfModeEnum.Auto})
                cam.autofocus_cycle()
            cam.switch_mode_and_capture_file(self._still_cfg, str(path))
            self.capture_finished.emit(str(path))
        except Exception as exc:  # pragma: no cover - hardware
            self.capture_failed.emit(f"Capture failed: {exc}")
        finally:
            if self._has_af:
                try:
                    cam.set_controls({"AfMode": self._controls.AfModeEnum.Continuous})
                except Exception:
                    pass


# ---------------------------------------------------------------------------
def create_camera(mode: str = "auto") -> CameraBackend:
    """``mode``: auto | pi | sim.

    auto: use the Pi camera when Picamera2 is importable (i.e. on the Pi),
    otherwise simulate. On the Pi with no camera attached the result is an
    UnavailableCamera, never a silent simulation.
    """
    if mode == "sim":
        return SimulatedCamera()
    try:
        from picamera2 import Picamera2  # type: ignore
        from libcamera import controls  # type: ignore
    except ImportError:
        if mode == "pi":
            return UnavailableCamera("Picamera2 is not installed.")
        return SimulatedCamera()

    try:
        if not Picamera2.global_camera_info():
            return UnavailableCamera(
                "No camera found on the camera connector. Check the ribbon "
                "cable, then restart the device."
            )
        return PiCamera(Picamera2(), controls)
    except Exception as exc:  # pragma: no cover - hardware
        return UnavailableCamera(f"Camera could not be opened: {exc}")
