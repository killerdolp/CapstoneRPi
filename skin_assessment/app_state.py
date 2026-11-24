"""Application state and data model, persisted in SQLite.

Sessions are stored in a ``sessions`` table::

    id              INTEGER PRIMARY KEY AUTOINCREMENT  -> shown as SES-000123
    image_url       TEXT, NULL when there is no photo
    skin_type       TEXT
    erythema_grade  TEXT
    saved_at        TEXT (ISO 8601), first save
    updated_at      TEXT (ISO 8601), most recent save

SQLite has no automatic timestamp columns, so the app writes ``saved_at`` on
insert and ``updated_at`` on every save. A session counts as edited once
``updated_at`` is later than ``saved_at``.

Photos live in ``photos/`` next to the database. A capture is a draft: it is
written to ``photos/pending.jpg`` and nothing else changes. Only
``save_session(..., commit_photo=True)`` (Confirm & Save) moves it to
``photos/SES-000123.jpg``, sets ``image_url`` (relative to the database
folder) and updates the database. Every other exit discards the draft.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Option values from the Whyre Figma design.
SKIN_TYPES = ["1", "2", "3", "4", "5", "6"]
ERYTHEMA_GRADES = ["0", "±", "+", "++"]

DEFAULT_DB_PATH = Path(
    os.environ.get("SKIN_ASSESSMENT_DB", Path.home() / "skin_assessment_data" / "sessions.db")
)

ID_PREFIX = "SES-"

# Export schema version. Provisional until the data schema is signed off.
SCHEMA_VERSION = "1.0"


def format_session_id(number: int) -> str:
    return f"{ID_PREFIX}{number:06d}"


def parse_session_id(session_id: str) -> int:
    return int(session_id[len(ID_PREFIX):])


PHOTO_DIR = "photos"
PENDING_PHOTO = "pending.jpg"


def photo_path_for(session_id: str) -> str:
    """Where a session's photo is stored, relative to the database folder."""
    return f"{PHOTO_DIR}/{session_id}.jpg"


def _display_time(value: Optional[datetime]) -> str:
    # e.g. "13 Oct 2026, 10:30 AM"
    return value.strftime("%d %b %Y, %I:%M %p") if value else "—"


@dataclass
class Session:
    """A single patient assessment session."""

    session_id: str
    skin_type: Optional[str] = None        # one of SKIN_TYPES, or None if unset
    erythema_grade: Optional[str] = None   # one of ERYTHEMA_GRADES, or None
    image_url: Optional[str] = None        # None when no photo was taken
    saved_at: Optional[datetime] = None    # first save
    updated_at: Optional[datetime] = None  # most recent save

    @property
    def has_photo(self) -> bool:
        return self.image_url is not None

    @property
    def is_complete(self) -> bool:
        return (
            self.skin_type is not None
            and self.erythema_grade is not None
            and self.has_photo
        )

    @property
    def status_label(self) -> str:
        return "Complete" if self.is_complete else "Incomplete"

    @property
    def was_edited(self) -> bool:
        return (
            self.saved_at is not None
            and self.updated_at is not None
            and self.updated_at > self.saved_at
        )

    @property
    def saved_at_display(self) -> str:
        return _display_time(self.saved_at)

    @property
    def updated_at_display(self) -> str:
        return _display_time(self.updated_at)

    def field_or_dash(self, value: Optional[str]) -> str:
        return value if value else "—"

    def copy(self) -> "Session":
        return replace(self)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url       TEXT,
    skin_type       TEXT,
    erythema_grade  TEXT,
    saved_at        TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
"""


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


class SessionStore:
    """Thin SQLite wrapper for the sessions table."""

    def __init__(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._db = sqlite3.connect(str(path))
        self._db.row_factory = sqlite3.Row
        with self._db:
            self._db.execute(_SCHEMA)

    def close(self) -> None:
        self._db.close()

    def all(self) -> List[Session]:
        rows = self._db.execute("SELECT * FROM sessions ORDER BY id").fetchall()
        return [self._from_row(r) for r in rows]

    def load(self, number: int) -> Optional[Session]:
        row = self._db.execute("SELECT * FROM sessions WHERE id = ?", (number,)).fetchone()
        return self._from_row(row) if row else None

    def next_number(self) -> int:
        """The number AUTOINCREMENT will assign to the next inserted row."""
        row = self._db.execute(
            "SELECT seq FROM sqlite_sequence WHERE name = 'sessions'"
        ).fetchone()
        return (row["seq"] if row else 0) + 1

    def insert(self, session: Session, now: datetime) -> None:
        with self._db:
            self._db.execute(
                "INSERT INTO sessions (id, image_url, skin_type, erythema_grade, saved_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    parse_session_id(session.session_id),
                    session.image_url,
                    session.skin_type,
                    session.erythema_grade,
                    _iso(now),
                    _iso(now),
                ),
            )

    def update(self, session: Session, now: datetime) -> None:
        with self._db:
            self._db.execute(
                "UPDATE sessions SET image_url = ?, skin_type = ?, erythema_grade = ?,"
                " updated_at = ? WHERE id = ?",
                (
                    session.image_url,
                    session.skin_type,
                    session.erythema_grade,
                    _iso(now),
                    parse_session_id(session.session_id),
                ),
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Session:
        return Session(
            session_id=format_session_id(row["id"]),
            image_url=row["image_url"],
            skin_type=row["skin_type"],
            erythema_grade=row["erythema_grade"],
            saved_at=datetime.fromisoformat(row["saved_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


class AppState:
    """Holds the session store and global device status."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH, demo: bool = False) -> None:
        self.ssd_connected: bool = True
        self.store = SessionStore(db_path)
        self.data_dir = self.store.path.parent
        (self.data_dir / PHOTO_DIR).mkdir(parents=True, exist_ok=True)
        self.discard_pending_photo()  # left over if the app stopped mid-capture
        if demo and not self.store.all():
            self._seed()

    # ---- seeding ----------------------------------------------------------
    def _seed(self) -> None:
        """Demo data: the four sample sessions from the wireframe."""
        samples = [
            (None, None, False, datetime(2026, 10, 9, 9, 12)),
            ("3", "+", True, datetime(2026, 10, 9, 14, 20)),
            (None, None, False, datetime(2026, 10, 12, 11, 5)),
            ("3", "+", True, datetime(2026, 10, 12, 16, 42)),
        ]
        from .camera import render_scene  # demo photos only

        for i, (skin, grade, photo, when) in enumerate(samples):
            sid = self.next_session_id()
            if photo:
                render_scene(1600, 1200, t=i * 1.7, seed=11 + i).save(
                    str(self.data_dir / photo_path_for(sid)), "JPG", 95
                )
            self.store.insert(
                Session(
                    session_id=sid,
                    skin_type=skin,
                    erythema_grade=grade,
                    image_url=photo_path_for(sid) if photo else None,
                ),
                when,
            )

    # ---- queries ----------------------------------------------------------
    @property
    def sessions(self) -> List[Session]:
        return self.store.all()

    def complete_sessions(self) -> List[Session]:
        return [s for s in self.sessions if s.is_complete]

    def incomplete_sessions(self) -> List[Session]:
        return [s for s in self.sessions if not s.is_complete]

    def summary_text(self) -> str:
        sessions = self.sessions
        total = len(sessions)
        complete = sum(1 for s in sessions if s.is_complete)
        return (
            f"Sessions saved on device: {total} "
            f"({complete} complete, {total - complete} incomplete)"
        )

    def get(self, session_id: str) -> Optional[Session]:
        try:
            return self.store.load(parse_session_id(session_id))
        except ValueError:
            return None

    # ---- draft photo ------------------------------------------------------
    @property
    def pending_photo_path(self) -> Path:
        """The single draft capture. Overwritten by each capture."""
        return self.data_dir / PHOTO_DIR / PENDING_PHOTO

    def discard_pending_photo(self) -> None:
        self.pending_photo_path.unlink(missing_ok=True)

    def photo_file(self, session: Session) -> Optional[Path]:
        """Absolute path of a session's saved photo, or None."""
        return self.data_dir / session.image_url if session.image_url else None

    # ---- mutations --------------------------------------------------------
    def next_session_id(self) -> str:
        """The ID the database will give the next new session."""
        return format_session_id(self.store.next_number())

    def save_session(
        self,
        session: Session,
        now: Optional[datetime] = None,
        commit_photo: bool = False,
    ) -> Session:
        """Insert a new session or update an existing one; return the stored row.

        With commit_photo, the draft photo becomes the session's photo: it is
        moved to photos/<id>.jpg, then the database is updated. If the
        database write fails, the file change is undone. Without
        commit_photo, any draft photo is discarded and image_url is unchanged.
        """
        now = now or datetime.now()
        pending = self.pending_photo_path
        if not (commit_photo and pending.exists()):
            self.discard_pending_photo()
            return self._write(session, now)

        rel = photo_path_for(session.session_id)
        final = self.data_dir / rel
        backup = final.with_name(final.name + ".bak")
        had_old = final.exists()

        with open(pending, "rb+") as f:  # make sure the capture is on disk
            os.fsync(f.fileno())
        if had_old:
            os.replace(final, backup)  # keep the old photo until the DB is updated
        os.replace(pending, final)
        try:
            row = self._write(replace(session, image_url=rel), now)
        except Exception:
            final.unlink(missing_ok=True)
            if had_old:
                os.replace(backup, final)
            raise
        if had_old:
            backup.unlink(missing_ok=True)
        session.image_url = rel
        return row

    def _write(self, session: Session, now: datetime) -> Session:
        number = parse_session_id(session.session_id)
        if self.store.load(number) is not None:
            self.store.update(session, now)
        else:
            self.store.insert(session, now)
        return self.store.load(number)
