import json
import sqlite3
from pathlib import Path

import packaging.version

from bgmi import __version__
from bgmi.config import BGMI_PATH, cfg
from bgmi.utils import print_error, print_info, print_warning

old_version_file = BGMI_PATH.joinpath("old")


def exec_sql(sql: str, db: Path = cfg.db_path) -> None:
    try:
        print_info(f"Execute {sql}")
        conn = sqlite3.connect(db)
        conn.execute(sql)
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:  # pragma: no cover
        print_error("Execute SQL statement failed", stop=False)


def _get_table_columns(db: Path, table: str) -> list[str]:
    conn = sqlite3.connect(db)
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns


def _migrate_from_v4(db: Path = cfg.db_path) -> None:
    """Migrate database schema from v4 to v5."""
    print_info("Migrating database from v4 to v5...")
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # --- bangumi table ---
    # v4: id INTEGER, name, subtitle_group, keyword, update_time, cover, status
    # v5: id TEXT, name, subtitle_group (JSON), update_day, cover, status
    v4_columns = _get_table_columns(db, "bangumi")

    if "keyword" in v4_columns or "update_time" in v4_columns:
        print_info("Migrating bangumi table: recreate with v5 schema")
        update_day_col = "update_day" if "update_day" in v4_columns else "update_time"
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bangumi_new (
                id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL UNIQUE,
                subtitle_group TEXT NOT NULL DEFAULT '[]',
                update_day CHAR(5) NOT NULL DEFAULT 'Unknown',
                cover TEXT NOT NULL DEFAULT '',
                status INTEGER NOT NULL DEFAULT 0
            )
        """)
        cursor.execute(f"""
            INSERT OR IGNORE INTO bangumi_new (id, name, subtitle_group, update_day, cover, status)
            SELECT CAST(id AS TEXT), name, subtitle_group,
                   COALESCE({update_day_col}, 'Unknown'),
                   cover, status
            FROM bangumi
        """)
        cursor.execute("DROP TABLE bangumi")
        cursor.execute("ALTER TABLE bangumi_new RENAME TO bangumi")

    # --- followed table ---
    # v4: id INTEGER PK, bangumi_name, episode (int), status, updated_time
    # v5: bangumi_name TEXT PK, episodes (JSON set), status, updated_time,
    #     subtitle (JSON), include (JSON), exclude (JSON), regex, season, is_script
    v4_followed_cols = _get_table_columns(db, "followed")

    if "episode" in v4_followed_cols and "episodes" not in v4_followed_cols:
        print_info("Migrating followed table: episode (scalar) -> episodes (set), merge filter")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS followed_new (
                bangumi_name TEXT PRIMARY KEY NOT NULL,
                episodes TEXT NOT NULL DEFAULT '[]',
                status INTEGER NOT NULL DEFAULT 1,
                updated_time INTEGER NOT NULL DEFAULT 0,
                subtitle TEXT NOT NULL DEFAULT '[]',
                "include" TEXT NOT NULL DEFAULT '[]',
                "exclude" TEXT NOT NULL DEFAULT '[]',
                regex TEXT NOT NULL DEFAULT '',
                season INTEGER NOT NULL DEFAULT 1,
                is_script INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Read v4 followed + filter data
        rows = cursor.execute("SELECT bangumi_name, episode, status, updated_time FROM followed").fetchall()
        for bangumi_name, episode, status, updated_time in rows:
            episodes = json.dumps(list(range(1, episode + 1))) if episode else "[]"

            # Try to get filter data
            filter_row = cursor.execute(
                "SELECT subtitle, include, exclude, regex FROM filter WHERE bangumi_name = ?",
                (bangumi_name,),
            ).fetchone()

            subtitle = "[]"
            include = "[]"
            exclude = "[]"
            regex = ""
            if filter_row:
                subtitle = filter_row[0] if filter_row[0] else "[]"
                include = filter_row[1] if filter_row[1] else "[]"
                exclude = filter_row[2] if filter_row[2] else "[]"
                regex = filter_row[3] if filter_row[3] else ""
                # v4 stored comma-separated strings, v5 uses JSON arrays
                if subtitle and not subtitle.startswith("["):
                    subtitle = json.dumps([s.strip() for s in subtitle.split(",") if s.strip()])
                if include and not include.startswith("["):
                    include = json.dumps([s.strip() for s in include.split(",") if s.strip()])
                if exclude and not exclude.startswith("["):
                    exclude = json.dumps([s.strip() for s in exclude.split(",") if s.strip()])

            cursor.execute(
                """INSERT OR IGNORE INTO followed_new 
                   (bangumi_name, episodes, status, updated_time, subtitle, "include", "exclude", regex)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (bangumi_name, episodes, status, updated_time or 0, subtitle, include, exclude, regex),
            )

        cursor.execute("DROP TABLE followed")
        cursor.execute("ALTER TABLE followed_new RENAME TO followed")

    # --- download table ---
    # v4: id, name, title, episode, download, status, created_time
    # v5: id, bangumi_name, title, episode, download, status, task_id
    v4_download_cols = _get_table_columns(db, "download")

    if "name" in v4_download_cols and "bangumi_name" not in v4_download_cols:
        print_info("Migrating download table: rename name -> bangumi_name, add task_id")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS download_new (
                id INTEGER PRIMARY KEY NOT NULL,
                bangumi_name TEXT NOT NULL,
                title TEXT NOT NULL,
                episode INTEGER NOT NULL,
                download TEXT NOT NULL,
                status INTEGER NOT NULL,
                task_id TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO download_new (id, bangumi_name, title, episode, download, status)
            SELECT id, name, title, episode, download, status FROM download
        """)
        cursor.execute("DROP TABLE download")
        cursor.execute("ALTER TABLE download_new RENAME TO download")
    elif "task_id" not in v4_download_cols:
        cursor.execute("ALTER TABLE download ADD COLUMN task_id TEXT")

    # --- drop filter table (merged into followed) ---
    cursor.execute("DROP TABLE IF EXISTS filter")

    conn.commit()
    conn.close()
    print_info("Migration from v4 to v5 completed successfully!")


def update_database() -> None:
    if not old_version_file.exists():
        old_version_file.write_text(__version__, encoding="utf8")
        return

    previous = packaging.version.parse(old_version_file.read_text(encoding="utf8").strip())

    if previous < packaging.version.Version("5.0.0a0"):
        print_warning("Detected v4 database, performing migration to v5...")
        _migrate_from_v4()

    if previous < packaging.version.Version("5.0.0a4"):
        followed_cols = _get_table_columns(cfg.db_path, "followed")
        if "season" not in followed_cols:
            exec_sql("ALTER TABLE followed ADD COLUMN season INTEGER NOT NULL DEFAULT 1")
        download_cols = _get_table_columns(cfg.db_path, "download")
        if "task_id" not in download_cols:
            exec_sql("ALTER TABLE download ADD COLUMN task_id TEXT")

    # all upgrade done, write current version
    old_version_file.write_text(__version__, encoding="utf8")
