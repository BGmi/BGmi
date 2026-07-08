import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

import packaging.version

from bgmi import __version__
from bgmi.config import BGMI_PATH, cfg
from bgmi.utils import print_error, print_info, print_warning
from bgmi.website.model import WebsiteBangumi

old_version_file = BGMI_PATH.joinpath("old")
SOURCE_ID_MIGRATION_VERSION = packaging.version.Version("5.0.0a4")


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


def _fix_json_column(cursor: sqlite3.Cursor, table: str, pk_col: str, col: str) -> None:
    """Convert non-JSON column values (empty strings, comma-separated) to JSON arrays."""
    for row in cursor.execute(f"SELECT {pk_col}, {col} FROM {table}").fetchall():
        val = row[1]
        if not val or val == "":
            cursor.execute(f"UPDATE {table} SET {col} = '[]' WHERE {pk_col} = ?", (row[0],))
        elif not val.startswith("["):
            fixed = json.dumps([s.strip() for s in val.split(",") if s.strip()])
            cursor.execute(f"UPDATE {table} SET {col} = ? WHERE {pk_col} = ?", (fixed, row[0]))
        else:
            try:
                json.loads(val)
            except json.JSONDecodeError:
                fixed = json.dumps([val])
                cursor.execute(f"UPDATE {table} SET {col} = ? WHERE {pk_col} = ?", (fixed, row[0]))


def _v4_bangumi_id_expr(columns: list[str]) -> str:
    if "keyword" in columns:
        return "COALESCE(NULLIF(keyword, ''), CAST(id AS TEXT))"
    return "CAST(id AS TEXT)"


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
        id_expr = _v4_bangumi_id_expr(v4_columns)
        update_day_col = "update_day" if "update_day" in v4_columns else "update_time"
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bangumi_new (
                id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL UNIQUE,
                subtitle_group TEXT NOT NULL DEFAULT '[]',
                update_day CHAR(5) NOT NULL DEFAULT 'Unknown',
                cover TEXT NOT NULL DEFAULT '',
                status INTEGER NOT NULL DEFAULT 0
            )
        """
        )
        cursor.execute(
            f"""
            INSERT OR IGNORE INTO bangumi_new (id, name, subtitle_group, update_day, cover, status)
            SELECT {id_expr}, name,
                   CASE WHEN subtitle_group = '' OR subtitle_group IS NULL THEN '[]' ELSE subtitle_group END,
                   COALESCE({update_day_col}, 'Unknown'),
                   cover, status
            FROM bangumi
        """
        )
        cursor.execute("DROP TABLE bangumi")
        cursor.execute("ALTER TABLE bangumi_new RENAME TO bangumi")

    # --- followed table ---
    # v4: id INTEGER PK, bangumi_name, episode (int), status, updated_time
    # v5: bangumi_name TEXT PK, episodes (JSON set), status, updated_time,
    #     subtitle (JSON), include (JSON), exclude (JSON), regex, season, is_script
    v4_followed_cols = _get_table_columns(db, "followed")

    if "episode" in v4_followed_cols and "episodes" not in v4_followed_cols:
        print_info("Migrating followed table: episode (scalar) -> episodes (set), merge filter")

        cursor.execute(
            """
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
                episode_offset INTEGER NOT NULL DEFAULT 0,
                display_name TEXT NOT NULL DEFAULT '',
                is_script INTEGER NOT NULL DEFAULT 0
            )
        """
        )

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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS download_new (
                id INTEGER PRIMARY KEY NOT NULL,
                bangumi_name TEXT NOT NULL,
                title TEXT NOT NULL,
                episode INTEGER NOT NULL,
                download TEXT NOT NULL,
                status INTEGER NOT NULL,
                task_id TEXT
            )
        """
        )
        cursor.execute(
            """
            INSERT INTO download_new (id, bangumi_name, title, episode, download, status)
            SELECT id, name, title, episode, download, status FROM download
        """
        )
        cursor.execute("DROP TABLE download")
        cursor.execute("ALTER TABLE download_new RENAME TO download")
    elif "task_id" not in v4_download_cols:
        cursor.execute("ALTER TABLE download ADD COLUMN task_id TEXT")

    # --- drop filter table (merged into followed) ---
    cursor.execute("DROP TABLE IF EXISTS filter")

    # --- fix non-JSON values in JSON columns ---
    _fix_json_column(cursor, "bangumi", "id", "subtitle_group")
    _fix_json_column(cursor, "followed", "bangumi_name", "subtitle")
    _fix_json_column(cursor, "followed", "bangumi_name", '"include"')
    _fix_json_column(cursor, "followed", "bangumi_name", '"exclude"')
    cursor.execute("UPDATE followed SET episodes = '[]' WHERE episodes = '' OR episodes IS NULL")

    # Back-fill season numbers from bangumi names
    from bgmi.lib.season import parse_season

    for row in cursor.execute("SELECT bangumi_name FROM followed").fetchall():
        detected = parse_season(row[0])
        if detected != 1:
            cursor.execute("UPDATE followed SET season = ? WHERE bangumi_name = ?", (detected, row[0]))

    conn.commit()
    conn.close()

    # Rename cover directory to .cover
    old_cover = Path(cfg.save_path) / "cover"
    new_cover = Path(cfg.save_path) / ".cover"
    if old_cover.is_dir() and not new_cover.exists():
        old_cover.rename(new_cover)
        print_info(f"Renamed cover directory: {old_cover} -> {new_cover}")

    print_info("Migration from v4 to v5 completed successfully!")

    # Refresh metadata from the data source. This is best-effort: the v4 keyword
    # has already been migrated into bangumi.id, so install should not fail here.
    print_info("Refreshing bangumi metadata from data source...")
    try:
        from bgmi.lib.fetch import website

        website.fetch(group_by_weekday=False)
        print_info("Bangumi IDs refreshed successfully.")
    except (Exception, SystemExit) as e:
        print_warning(f"Failed to refresh bangumi IDs (can fix later with `bgmi cal --update`): {e}")


def _needs_v4_migration(db: Path = cfg.db_path) -> bool:
    """Detect v4 schema by checking for v4-specific columns regardless of version file."""
    if not db.exists():
        return False
    cols = _get_table_columns(db, "bangumi")
    if "keyword" in cols or "update_time" in cols:
        return True
    followed_cols = _get_table_columns(db, "followed")
    if "episode" in followed_cols and "episodes" not in followed_cols:
        return True
    return False


def _find_source_id_mismatches(
    source_bangumi: Sequence[WebsiteBangumi], db: Path = cfg.db_path
) -> list[tuple[str, str, str]]:
    if not db.exists():
        return []

    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT name, id FROM bangumi").fetchall()
    finally:
        conn.close()

    current_ids = {name: str(bangumi_id) for name, bangumi_id in rows}
    return [
        (bangumi.name, current_ids[bangumi.name], str(bangumi.id))
        for bangumi in source_bangumi
        if bangumi.name in current_ids and current_ids[bangumi.name] != str(bangumi.id)
    ]


def _refresh_legacy_bangumi_ids_if_needed(db: Path = cfg.db_path) -> None:
    try:
        from bgmi.lib.fetch import website

        source_bangumi = website.fetch_bangumi_calendar()
    except (Exception, SystemExit) as e:
        print_warning(f"Failed to check legacy bangumi IDs (fix with `bgmi cal --update`): {e}")
        return

    if not source_bangumi:
        return

    mismatches = _find_source_id_mismatches(source_bangumi, db=db)
    if not mismatches:
        return

    names = ", ".join(name for name, _, _ in mismatches[:3])
    if len(mismatches) > 3:
        names += ", ..."
    print_warning(f"Bangumi source IDs differ from data source ({names}), refreshing...")
    try:
        website.fetch(group_by_weekday=False)
        print_info("Bangumi IDs refreshed successfully.")
    except (Exception, SystemExit) as e:
        print_warning(f"Failed to refresh bangumi IDs (fix with `bgmi cal --update`): {e}")


def update_database() -> None:
    if not old_version_file.exists():
        if _needs_v4_migration(cfg.db_path):
            print_warning("Detected v4 database (no version file), performing migration to v5...")
            _migrate_from_v4(cfg.db_path)
        old_version_file.write_text(__version__, encoding="utf8")
        return

    previous = packaging.version.parse(old_version_file.read_text(encoding="utf8").strip())
    migrated_from_v4 = False

    if previous < packaging.version.Version("5.0.0a0") or _needs_v4_migration(cfg.db_path):
        print_warning("Detected v4 database, performing migration to v5...")
        _migrate_from_v4(cfg.db_path)
        migrated_from_v4 = True

    if previous < SOURCE_ID_MIGRATION_VERSION:
        followed_cols = _get_table_columns(cfg.db_path, "followed")
        if "season" not in followed_cols:
            exec_sql("ALTER TABLE followed ADD COLUMN season INTEGER NOT NULL DEFAULT 1", db=cfg.db_path)
        if "episode_offset" not in followed_cols:
            exec_sql("ALTER TABLE followed ADD COLUMN episode_offset INTEGER NOT NULL DEFAULT 0", db=cfg.db_path)
        if "display_name" not in followed_cols:
            exec_sql("ALTER TABLE followed ADD COLUMN display_name TEXT NOT NULL DEFAULT ''", db=cfg.db_path)
        download_cols = _get_table_columns(cfg.db_path, "download")
        if "task_id" not in download_cols:
            exec_sql("ALTER TABLE download ADD COLUMN task_id TEXT", db=cfg.db_path)

    # Ensure scripts table has all expected columns
    scripts_cols = _get_table_columns(cfg.db_path, "scripts")
    if scripts_cols:
        if "episodes" not in scripts_cols:
            exec_sql("ALTER TABLE scripts ADD COLUMN episodes TEXT NOT NULL DEFAULT '[]'", db=cfg.db_path)
        if "updated_time" not in scripts_cols:
            exec_sql("ALTER TABLE scripts ADD COLUMN updated_time INTEGER NOT NULL DEFAULT 0", db=cfg.db_path)
        if "update_day" not in scripts_cols:
            exec_sql("ALTER TABLE scripts ADD COLUMN update_day TEXT NOT NULL DEFAULT 'Unknown'", db=cfg.db_path)
        if "cover" not in scripts_cols:
            exec_sql("ALTER TABLE scripts ADD COLUMN cover TEXT NOT NULL DEFAULT ''", db=cfg.db_path)

    # Older v5 prereleases copied the v4 local auto-increment id into bangumi.id.
    # Compare against the current data source once instead of guessing by id shape.
    if previous < SOURCE_ID_MIGRATION_VERSION and not migrated_from_v4:
        _refresh_legacy_bangumi_ids_if_needed(cfg.db_path)

    # all upgrade done, write current version
    old_version_file.write_text(__version__, encoding="utf8")
