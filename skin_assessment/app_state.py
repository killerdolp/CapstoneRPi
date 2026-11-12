"""Data model, on-device persistence and global device status.

Storage layout (under the data directory)::

    sessions/S-0001.json      one record per session (atomic writes)
    photos/S-0001_r1.jpg      one photo per saved revision; never deleted
    pending/capture.jpg       the most recent un-confirmed capture

Records are never silently altered: each save bumps ``revision`` and a
retaken photo is written under a new revision filename, so earlier photos
remain on disk for audit.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal

# Erythema grade options as defined by the clinical protocol.
ERYTHEMA_GRADES = ["0", "±", "+", "++", "+++"]
# Skin type (Fitzpatrick 2-6) options.
SKIN_TYPES = ["2", "3", "4", "5", "6"]

# Export schema version. Provisional until the data schema is signed off.
SCHEMA_VERSION = "1.0"

DEFAULT_DATA_DIR = Path(
    os.environ.get("SKIN_ASSESSMENT_DATA", Path.home() / "skin_assessment_data")
)


def _fmt(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    return f"{dt.day} {dt.strftime('%b %Y, %H:%M')}"


@dataclass
class Session:
    """A single patient assessment session."""

    session_id: str
    skin_type: Optional[str] = None
    erythema_grade: Optional[str] = None
    photo_file: Optional[str] = None
    created_at: Optional[datetime] = None
    saved_at: Optional[datetime] = None
    revision: int = 0
    demo: bool = False
    # Runtime-only fields (not persisted).
    photo_path: Optional[Path] = field(default=None, compare=False, repr=False)

    @property
    def has_photo(self) -> bool:
        return self.photo_path is not None and self.photo_path.exists()

    @property
    def is_complete(self) -> bool:
        return (
            self.skin_type is not None
            and self.erythema_grade is not None
            and self.has_photo
        )

    @property
    def status_label(self) -> str:
        return "COMPLETE" if self.is_complete else "INCOMPLETE"

    @property
    def saved_at_display(self) -> str:
        return _fmt(self.saved_at)

    @property
    def created_at_display(self) -> str:
        return _fmt(self.created_at)

    def missing_fields(self) -> List[str]:
        missing = []
        if self.skin_type is None:
            missing.append("skin type")
        if self.erythema_grade is None:
            missing.append("erythema grade")
        if not self.has_photo:
            missing.append("photo")
        return missing

    @staticmethod
    def field_or_dash(value: Optional[str]) -> str:
        return value if value else "—"

    def copy(self) -> "Session":
        return replace(self)

    # ---- serialisation ---------------------------------------------------
    def to_dict(self) -> Dict:
        data = asdict(self)
        data.pop("photo_path", None)
        for key in ("created_at", "saved_at"):
            value = getattr(self, key)
            data[key] = value.isoformat(timespec="seconds") if value else None
        data["status"] = self.status_label.lower()
        data["schema_version"] = SCHEMA_VERSION
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        def dt(value):
            return datetime.fromisoformat(value) if value else None

        return cls(
            session_id=data["session_id"],
            skin_type=data.get("skin_type"),
            erythema_grade=data.get("erythema_grade"),
            photo_file=data.get("photo_file"),
            created_at=dt(data.get("created_at")),
            saved_at=dt(data.get("saved_at")),
            revision=int(data.get("revision", 0)),
            demo=bool(data.get("demo", False)),
        )


class SessionStore:
    """Durable JSON + JPEG storage for sessions on the device."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.sessions_dir = self.root / "sessions"
        self.photos_dir = self.root / "photos"
        self.pending_dir = self.root / "pending"
        for d in (self.sessions_dir, self.photos_dir, self.pending_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ---- reads -----------------------------------------------------------
    def load_all(self) -> List[Session]:
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                session = Session.from_dict(data)
            except (OSError, ValueError, KeyError) as exc:
                print(f"[store] skipped unreadable record {path.name}: {exc}")
                continue
            self._attach_photo(session)
            sessions.append(session)
        return sessions

    def _attach_photo(self, session: Session) -> None:
        session.photo_path = (
            self.photos_dir / session.photo_file if session.photo_file else None
        )

    def free_bytes(self) -> int:
        try:
            return shutil.disk_usage(self.root).free
        except OSError:
            return 0

    # ---- writes ----------------------------------------------------------
    def pending_photo_path(self) -> Path:
        return self.pending_dir / "capture.jpg"

    def discard_pending(self) -> None:
        try:
            self.pending_photo_path().unlink()
        except FileNotFoundError:
            pass

    def save(self, session: Session, pending_photo: Optional[Path] = None,
             now: Optional[datetime] = None) -> Session:
        """Persist ``session`` as a new revision and return the saved copy."""
        saved = session.copy()
        now = now or datetime.now().replace(microsecond=0)
        saved.revision = session.revision + 1
        saved.saved_at = now
        if saved.created_at is None:
            saved.created_at = now

        if pending_photo is not None and pending_photo.exists():
            name = f"{saved.session_id}_r{saved.revision}.jpg"
            target = self.photos_dir / name
            os.replace(pending_photo, target)
            _fsync_dir(self.photos_dir)
            saved.photo_file = name
        self._attach_photo(saved)

        _atomic_write_json(self.sessions_dir / f"{saved.session_id}.json", saved.to_dict())
        return saved


def _atomic_write_json(path: Path, data: Dict) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        _fsync_dir(path.parent)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _fsync_dir(directory: Path) -> None:
    if os.name != "posix":
        return
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class AppState(QObject):
    """Holds the session list and global device status."""

    changed = Signal()  # sessions or device status changed

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR, demo: bool = False) -> None:
        super().__init__()
        self.demo = demo
        self.store = SessionStore(data_dir)
        self.sessions: List[Session] = self.store.load_all()
        # Clinical SSD detection is not implemented yet; toggled with Ctrl+D.
        self.ssd_connected: bool = True

    # ---- queries ---------------------------------------------------------
    def complete_sessions(self) -> List[Session]:
        return [s for s in self.sessions if s.is_complete]

    def incomplete_sessions(self) -> List[Session]:
        return [s for s in self.sessions if not s.is_complete]

    def newest(self) -> Optional[Session]:
        dated = [s for s in self.sessions if s.saved_at]
        return max(dated, key=lambda s: s.saved_at) if dated else None

    def summary_text(self) -> str:
        total = len(self.sessions)
        complete = len(self.complete_sessions())
        return (
            f"Sessions saved on device: {total} "
            f"({complete} complete, {total - complete} incomplete)"
        )

    def get(self, session_id: str) -> Optional[Session]:
        for s in self.sessions:
            if s.session_id == session_id:
                return s
        return None

    def next_session_id(self) -> str:
        max_num = 0
        for s in self.sessions:
            try:
                max_num = max(max_num, int(s.session_id.split("-")[1]))
            except (IndexError, ValueError):
                continue
        return f"S-{max_num + 1:04d}"

    # ---- mutations -------------------------------------------------------
    def save(self, session: Session, pending_photo: Optional[Path] = None,
             now: Optional[datetime] = None) -> Session:
        saved = self.store.save(session, pending_photo, now)
        for i, existing in enumerate(self.sessions):
            if existing.session_id == saved.session_id:
                self.sessions[i] = saved
                break
        else:
            self.sessions.append(saved)
        self.changed.emit()
        return saved

    def set_ssd_connected(self, connected: bool) -> None:
        if connected != self.ssd_connected:
            self.ssd_connected = connected
            self.changed.emit()
