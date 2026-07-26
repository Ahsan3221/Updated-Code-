import sqlite3
import os
import threading
import json
from datetime import datetime
from contextlib import contextmanager


class DatabaseManager:
    """
    Thread-safe SQLite database manager V2.
    Includes workspace management + persona support.
    """

    def __init__(self, db_name="fb_automation_v3.db"):
        self.db_path = os.path.join(
            os.path.dirname(__file__), db_name
        )
        self.lock = threading.Lock()
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(
            self.db_path,
            timeout=30,
            check_same_thread=False,
            isolation_level=None
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self.lock:
            with self._get_conn() as conn:
                self._create_tables(conn)
                self._run_migrations(conn)

    def _create_tables(self, conn):
        conn.execute('''
            CREATE TABLE IF NOT EXISTS workspaces (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name    TEXT    UNIQUE NOT NULL,
                target_fb_url   TEXT,
                chrome_path     TEXT,
                proxy           TEXT,
                added_on        DATETIME,
                warmup_enabled  INTEGER DEFAULT 1,
                warmup_min      INTEGER DEFAULT 15,
                warmup_max      INTEGER DEFAULT 45,
                offset_enabled  INTEGER DEFAULT 1,
                offset_min      INTEGER DEFAULT 5,
                offset_max      INTEGER DEFAULT 25,
                persona_json    TEXT,
                is_pinned       INTEGER DEFAULT 0,
                is_archived     INTEGER DEFAULT 0,
                tags_json       TEXT,
                custom_color    TEXT,
                last_activity   DATETIME,
                description     TEXT
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS page_videos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_name  TEXT,
                source_url      TEXT,
                local_path      TEXT,
                title           TEXT,
                description     TEXT,
                schedule_time   TEXT,
                status          TEXT    DEFAULT "PENDING_DOWNLOAD",
                added_on        DATETIME,
                thumb_path      TEXT
            )
        ''')

    def _run_migrations(self, conn):
        workspace_cols = {
            "warmup_enabled" : "INTEGER DEFAULT 1",
            "warmup_min"     : "INTEGER DEFAULT 15",
            "warmup_max"     : "INTEGER DEFAULT 45",
            "offset_enabled" : "INTEGER DEFAULT 1",
            "offset_min"     : "INTEGER DEFAULT 5",
            "offset_max"     : "INTEGER DEFAULT 25",
            "persona_json"   : "TEXT",
            "is_pinned"      : "INTEGER DEFAULT 0",
            "is_archived"    : "INTEGER DEFAULT 0",
            "tags_json"      : "TEXT",
            "custom_color"   : "TEXT",
            "last_activity"  : "DATETIME",
            "description"    : "TEXT",
        }
        self._add_missing_columns(
            conn, "workspaces", workspace_cols
        )

        video_cols = {
            "thumb_path" : "TEXT",
            "local_path" : "TEXT",
        }
        self._add_missing_columns(
            conn, "page_videos", video_cols
        )

    def _add_missing_columns(
        self, conn, table, columns: dict
    ):
        existing = {
            row[1]
            for row in conn.execute(
                f"PRAGMA table_info({table})"
            )
        }
        for col_name, col_def in columns.items():
            if col_name not in existing:
                try:
                    conn.execute(
                        f"ALTER TABLE {table} "
                        f"ADD COLUMN {col_name} {col_def}"
                    )
                except sqlite3.OperationalError:
                    pass

    # ─────────────────────────────────────────────
    # WORKSPACE CRUD
    # ─────────────────────────────────────────────
    def add_workspace(
        self, profile_name, target_fb_url,
        chrome_path, proxy
    ):
        with self.lock:
            with self._get_conn() as conn:
                try:
                    row = conn.execute(
                        "SELECT id FROM workspaces "
                        "WHERE profile_name = ?",
                        (profile_name,)
                    ).fetchone()
                    if row:
                        return (
                            False,
                            "Workspace already exists!"
                        )

                    conn.execute('''
                        INSERT INTO workspaces
                            (profile_name, target_fb_url,
                             chrome_path, proxy, added_on,
                             last_activity)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        profile_name,
                        target_fb_url,
                        chrome_path,
                        proxy,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ))
                    return True, "Workspace created!"
                except sqlite3.IntegrityError:
                    return (
                        False,
                        "Workspace already exists!"
                    )

    def get_all_workspaces(self, include_archived=False):
        with self._get_conn() as conn:
            if include_archived:
                query = (
                    "SELECT profile_name, target_fb_url, "
                    "chrome_path, proxy, is_pinned, "
                    "is_archived, last_activity "
                    "FROM workspaces "
                    "ORDER BY is_pinned DESC, "
                    "added_on DESC"
                )
            else:
                query = (
                    "SELECT profile_name, target_fb_url, "
                    "chrome_path, proxy, is_pinned, "
                    "is_archived, last_activity "
                    "FROM workspaces "
                    "WHERE is_archived = 0 "
                    "ORDER BY is_pinned DESC, "
                    "added_on DESC"
                )
            rows = conn.execute(query).fetchall()
            return [tuple(r) for r in rows]

    def get_workspace_details(self, profile_name):
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM workspaces "
                "WHERE profile_name = ?",
                (profile_name,)
            ).fetchone()
            return tuple(row) if row else None

    def update_workspace(
        self, profile_name,
        target_fb_url, chrome_path, proxy,
        w_en=1, w_min=15, w_max=45,
        o_en=1, o_min=5, o_max=25
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute('''
                    UPDATE workspaces SET
                        target_fb_url  = COALESCE(
                            ?, target_fb_url),
                        chrome_path    = COALESCE(
                            ?, chrome_path),
                        proxy          = COALESCE(
                            ?, proxy),
                        warmup_enabled = ?,
                        warmup_min     = ?,
                        warmup_max     = ?,
                        offset_enabled = ?,
                        offset_min     = ?,
                        offset_max     = ?
                    WHERE profile_name = ?
                ''', (
                    target_fb_url, chrome_path, proxy,
                    int(w_en), int(w_min), int(w_max),
                    int(o_en), int(o_min), int(o_max),
                    profile_name,
                ))

    # ─────────────────────────────────────────────
    # WORKSPACE MANAGEMENT (NEW)
    # ─────────────────────────────────────────────
    def rename_workspace(
        self, old_name: str, new_name: str
    ) -> tuple:
        """Rename workspace and update video references."""
        new_name = new_name.strip()
        if not new_name:
            return False, "Name cannot be empty!"

        with self.lock:
            with self._get_conn() as conn:
                # Check duplicate
                existing = conn.execute(
                    "SELECT id FROM workspaces "
                    "WHERE profile_name = ?",
                    (new_name,)
                ).fetchone()
                if existing:
                    return (
                        False,
                        f"'{new_name}' already exists!"
                    )

                # Rename workspace
                conn.execute(
                    "UPDATE workspaces "
                    "SET profile_name = ? "
                    "WHERE profile_name = ?",
                    (new_name, old_name)
                )

                # Update video references
                conn.execute(
                    "UPDATE page_videos "
                    "SET workspace_name = ? "
                    "WHERE workspace_name = ?",
                    (new_name, old_name)
                )

                return True, f"Renamed to '{new_name}'!"

    def delete_workspace(
        self, profile_name: str,
        delete_videos: bool = True
    ) -> tuple:
        """Delete workspace and optionally its videos."""
        with self.lock:
            with self._get_conn() as conn:
                try:
                    if delete_videos:
                        conn.execute(
                            "DELETE FROM page_videos "
                            "WHERE workspace_name = ?",
                            (profile_name,)
                        )
                    conn.execute(
                        "DELETE FROM workspaces "
                        "WHERE profile_name = ?",
                        (profile_name,)
                    )
                    return True, "Workspace deleted!"
                except Exception as e:
                    return False, f"Delete failed: {e}"

    def duplicate_workspace(
        self, source_name: str, new_name: str
    ) -> tuple:
        """Duplicate workspace settings (no videos)."""
        with self.lock:
            with self._get_conn() as conn:
                source = conn.execute(
                    "SELECT * FROM workspaces "
                    "WHERE profile_name = ?",
                    (source_name,)
                ).fetchone()

                if not source:
                    return False, "Source not found!"

                existing = conn.execute(
                    "SELECT id FROM workspaces "
                    "WHERE profile_name = ?",
                    (new_name,)
                ).fetchone()
                if existing:
                    return (
                        False,
                        f"'{new_name}' already exists!"
                    )

                try:
                    conn.execute('''
                        INSERT INTO workspaces
                            (profile_name, target_fb_url,
                             chrome_path, proxy, added_on,
                             warmup_enabled, warmup_min,
                             warmup_max, offset_enabled,
                             offset_min, offset_max,
                             last_activity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?,
                                ?, ?, ?, ?)
                    ''', (
                        new_name,
                        source[2],  # target_fb_url
                        "",  # chrome_path (new needed)
                        source[4],  # proxy
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        source[6], source[7], source[8],
                        source[9], source[10], source[11],
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ))
                    return True, f"Duplicated as '{new_name}'!"
                except Exception as e:
                    return False, f"Duplicate failed: {e}"

    def toggle_pin_workspace(
        self, profile_name: str
    ) -> bool:
        """Toggle pin/unpin state."""
        with self.lock:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT is_pinned FROM workspaces "
                    "WHERE profile_name = ?",
                    (profile_name,)
                ).fetchone()
                if row is None:
                    return False
                new_val = 0 if row[0] else 1
                conn.execute(
                    "UPDATE workspaces "
                    "SET is_pinned = ? "
                    "WHERE profile_name = ?",
                    (new_val, profile_name)
                )
                return bool(new_val)

    def toggle_archive_workspace(
        self, profile_name: str
    ) -> bool:
        """Toggle archive state."""
        with self.lock:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT is_archived FROM workspaces "
                    "WHERE profile_name = ?",
                    (profile_name,)
                ).fetchone()
                if row is None:
                    return False
                new_val = 0 if row[0] else 1
                conn.execute(
                    "UPDATE workspaces "
                    "SET is_archived = ? "
                    "WHERE profile_name = ?",
                    (new_val, profile_name)
                )
                return bool(new_val)

    def update_workspace_tags(
        self, profile_name: str, tags: list
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE workspaces "
                    "SET tags_json = ? "
                    "WHERE profile_name = ?",
                    (json.dumps(tags), profile_name)
                )

    def get_workspace_tags(
        self, profile_name: str
    ) -> list:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT tags_json FROM workspaces "
                "WHERE profile_name = ?",
                (profile_name,)
            ).fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except Exception:
                    return []
            return []

    def update_last_activity(self, profile_name: str):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE workspaces "
                    "SET last_activity = ? "
                    "WHERE profile_name = ?",
                    (
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        profile_name
                    )
                )

    def get_workspace_stats(
        self, profile_name: str
    ) -> dict:
        """Get video stats for workspace."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT status FROM page_videos "
                "WHERE workspace_name = ?",
                (profile_name,)
            ).fetchall()

            stats = {
                "total"     : len(rows),
                "published" : 0,
                "pending"   : 0,
                "failed"    : 0,
                "processing": 0,
            }

            for row in rows:
                s = str(row[0] or "").upper()
                if "PUBLISHED" in s:
                    stats["published"] += 1
                elif "FAILED" in s or "STOPPED" in s:
                    stats["failed"] += 1
                elif any(x in s for x in [
                    "STARTING", "DOWNLOADING",
                    "EDITING", "UPLOADING",
                    "MERGING", "PAUSED"
                ]):
                    stats["processing"] += 1
                else:
                    stats["pending"] += 1

            return stats

    def search_workspaces(
        self, query: str
    ) -> list:
        """Search workspaces by name."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT profile_name, target_fb_url, "
                "chrome_path, proxy, is_pinned, "
                "is_archived, last_activity "
                "FROM workspaces "
                "WHERE profile_name LIKE ? "
                "AND is_archived = 0 "
                "ORDER BY is_pinned DESC, "
                "added_on DESC",
                (f"%{query}%",)
            ).fetchall()
            return [tuple(r) for r in rows]

    # ─────────────────────────────────────────────
    # PERSONA MANAGEMENT
    # ─────────────────────────────────────────────
    def save_workspace_persona(
        self, profile_name: str, persona_dict: dict
    ) -> bool:
        with self.lock:
            with self._get_conn() as conn:
                try:
                    conn.execute(
                        "UPDATE workspaces "
                        "SET persona_json = ? "
                        "WHERE profile_name = ?",
                        (
                            json.dumps(persona_dict),
                            profile_name
                        )
                    )
                    return True
                except Exception as e:
                    print(f"[-] Persona save error: {e}")
                    return False

    def get_workspace_persona(
        self, profile_name: str
    ) -> dict:
        with self._get_conn() as conn:
            try:
                row = conn.execute(
                    "SELECT persona_json FROM workspaces "
                    "WHERE profile_name = ?",
                    (profile_name,)
                ).fetchone()
                if row and row[0]:
                    return json.loads(row[0])
                return None
            except Exception:
                return None

    def delete_workspace_persona(
        self, profile_name: str
    ) -> bool:
        with self.lock:
            with self._get_conn() as conn:
                try:
                    conn.execute(
                        "UPDATE workspaces "
                        "SET persona_json = NULL "
                        "WHERE profile_name = ?",
                        (profile_name,)
                    )
                    return True
                except Exception:
                    return False

    # ─────────────────────────────────────────────
    # VIDEO QUEUE
    # ─────────────────────────────────────────────
    def add_video_to_queue(
        self, workspace_name, source_url
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute('''
                    INSERT INTO page_videos
                        (workspace_name, source_url,
                         status, added_on)
                    VALUES (?, ?, ?, ?)
                ''', (
                    workspace_name,
                    source_url,
                    "PENDING_DOWNLOAD",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                ))
                row = conn.execute(
                    "SELECT last_insert_rowid()"
                ).fetchone()

                # Update workspace last activity
                conn.execute(
                    "UPDATE workspaces "
                    "SET last_activity = ? "
                    "WHERE profile_name = ?",
                    (
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        workspace_name
                    )
                )

                return row[0] if row else None

    def get_videos_for_workspace(
        self, workspace_name
    ):
        with self._get_conn() as conn:
            rows = conn.execute('''
                SELECT
                    id, source_url, status,
                    schedule_time, title,
                    description, thumb_path,
                    local_path
                FROM page_videos
                WHERE workspace_name = ?
                ORDER BY added_on DESC
            ''', (workspace_name,)).fetchall()
            return [tuple(r) for r in rows]

    def get_video_details(self, video_id):
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM page_videos "
                "WHERE id = ?",
                (video_id,)
            ).fetchone()
            return tuple(row) if row else None

    def update_video_local_path(
        self, video_id, local_path
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE page_videos "
                    "SET local_path = ? WHERE id = ?",
                    (str(local_path).strip(), video_id)
                )

    def update_video_thumb_path(
        self, video_id, thumb_path
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE page_videos "
                    "SET thumb_path = ? WHERE id = ?",
                    (str(thumb_path).strip(), video_id)
                )

    def update_video_status(
        self, video_id, new_status
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE page_videos "
                    "SET status = ? WHERE id = ?",
                    (
                        str(new_status).strip().upper(),
                        video_id
                    )
                )

    def update_video_details(
        self, video_id, title, description,
        schedule_time
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute('''
                    UPDATE page_videos
                    SET title = ?, description = ?,
                        schedule_time = ?
                    WHERE id = ?
                ''', (
                    str(title).strip() if title else "",
                    str(description).strip()
                    if description else "",
                    str(schedule_time).strip()
                    if schedule_time else "NOW",
                    video_id,
                ))

    def delete_video(self, video_id):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute(
                    "DELETE FROM page_videos "
                    "WHERE id = ?",
                    (video_id,)
                )

    def get_video_count_by_status(
        self, workspace_name, status
    ):
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM page_videos "
                "WHERE workspace_name = ? "
                "AND status LIKE ?",
                (workspace_name, f"%{status.upper()}%")
            ).fetchone()
            return row[0] if row else 0

    def clear_workspace_videos(
        self, workspace_name
    ):
        with self.lock:
            with self._get_conn() as conn:
                conn.execute(
                    "DELETE FROM page_videos "
                    "WHERE workspace_name = ?",
                    (workspace_name,)
                )

    def close(self):
        pass


# Global singleton
db = DatabaseManager()