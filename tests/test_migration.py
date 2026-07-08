import sqlite3
from unittest import mock

import pytest

from bgmi import __version__
from bgmi.config import cfg
from bgmi.lib.update import (
    _find_source_id_mismatches,
    _get_table_columns,
    _migrate_from_v4,
    update_database,
)
from bgmi.website.model import WebsiteBangumi


@pytest.fixture()
def v4_db(tmp_path):
    """Create a minimal v4-style database for migration testing."""
    db_path = tmp_path / "bangumi.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE bangumi (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            subtitle_group TEXT NOT NULL DEFAULT '',
            keyword TEXT NOT NULL DEFAULT '',
            update_time CHAR(5) NOT NULL DEFAULT 'Unknown',
            cover TEXT NOT NULL DEFAULT '',
            status INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE followed (
            id INTEGER PRIMARY KEY,
            bangumi_name TEXT NOT NULL UNIQUE,
            episode INTEGER NOT NULL DEFAULT 0,
            status INTEGER NOT NULL DEFAULT 1,
            updated_time INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE filter (
            bangumi_name TEXT PRIMARY KEY,
            subtitle TEXT NOT NULL DEFAULT '',
            include TEXT NOT NULL DEFAULT '',
            exclude TEXT NOT NULL DEFAULT '',
            regex TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE download (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            episode INTEGER NOT NULL,
            download TEXT NOT NULL,
            status INTEGER NOT NULL
        );

        INSERT INTO bangumi (id, name, subtitle_group, keyword, update_time, cover, status)
        VALUES (1, 'TestAnime', '[]', 'test', 'Mon', '/cover/test.jpg', 0);

        INSERT INTO followed (bangumi_name, episode, status, updated_time)
        VALUES ('TestAnime', 5, 1, 1000);

        INSERT INTO filter (bangumi_name, subtitle, include, exclude, regex)
        VALUES ('TestAnime', 'sub1,sub2', 'keyword1', 'bad', '.*720.*');

        INSERT INTO download (id, name, title, episode, download, status)
        VALUES (1, 'TestAnime', 'TestAnime EP01', 1, 'magnet:?xt=test', 2);
    """
    )
    conn.close()
    return db_path


@pytest.fixture()
def scripts_db_missing_cols(tmp_path):
    """Create a database with scripts table missing the episodes column."""
    db_path = tmp_path / "bangumi.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE bangumi (
            id TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL UNIQUE,
            subtitle_group TEXT NOT NULL DEFAULT '[]',
            update_day CHAR(5) NOT NULL DEFAULT 'Unknown',
            cover TEXT NOT NULL DEFAULT '',
            status INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE followed (
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
        );
        CREATE TABLE download (
            id INTEGER PRIMARY KEY NOT NULL,
            bangumi_name TEXT NOT NULL,
            title TEXT NOT NULL,
            episode INTEGER NOT NULL,
            download TEXT NOT NULL,
            status INTEGER NOT NULL,
            task_id TEXT
        );
        CREATE TABLE scripts (
            bangumi_name TEXT PRIMARY KEY NOT NULL,
            status INTEGER NOT NULL DEFAULT 1
        );

        INSERT INTO scripts (bangumi_name, status) VALUES ('ScriptAnime', 1);
    """
    )
    conn.close()
    return db_path


def create_v5_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE bangumi (
            id TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL UNIQUE,
            subtitle_group TEXT NOT NULL DEFAULT '[]',
            update_day CHAR(5) NOT NULL DEFAULT 'Unknown',
            cover TEXT NOT NULL DEFAULT '',
            status INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE followed (
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
        );
        CREATE TABLE download (
            id INTEGER PRIMARY KEY NOT NULL,
            bangumi_name TEXT NOT NULL,
            title TEXT NOT NULL,
            episode INTEGER NOT NULL,
            download TEXT NOT NULL,
            status INTEGER NOT NULL,
            task_id TEXT
        );
        """
    )
    return conn


def test_migrate_from_v4_bangumi_table(v4_db, tmp_path):
    cover_dir = tmp_path / "save" / "cover"
    cover_dir.mkdir(parents=True)
    (cover_dir / "test.jpg").write_text("fake")

    with mock.patch.object(cfg, "save_path", tmp_path / "save"), mock.patch("bgmi.lib.fetch.website"):
        _migrate_from_v4(db=v4_db)

    cols = _get_table_columns(v4_db, "bangumi")
    assert "keyword" not in cols
    assert "update_time" not in cols
    assert "update_day" in cols
    assert "id" in cols

    conn = sqlite3.connect(v4_db)
    row = conn.execute("SELECT id, name, update_day FROM bangumi").fetchone()
    conn.close()
    assert row[0] == "test"
    assert row[1] == "TestAnime"
    assert row[2] == "Mon"


def test_migrate_from_v4_falls_back_to_local_id_when_keyword_empty(v4_db, tmp_path):
    conn = sqlite3.connect(v4_db)
    conn.execute("UPDATE bangumi SET keyword = '' WHERE name = 'TestAnime'")
    conn.commit()
    conn.close()

    with mock.patch.object(cfg, "save_path", tmp_path / "save"), mock.patch("bgmi.lib.fetch.website"):
        _migrate_from_v4(db=v4_db)

    conn = sqlite3.connect(v4_db)
    row = conn.execute("SELECT id FROM bangumi WHERE name = 'TestAnime'").fetchone()
    conn.close()
    assert row[0] == "1"


def test_migrate_from_v4_does_not_fail_when_metadata_refresh_exits(v4_db, tmp_path):
    with (
        mock.patch.object(cfg, "save_path", tmp_path / "save"),
        mock.patch("bgmi.lib.fetch.website") as website,
    ):
        website.fetch.side_effect = SystemExit(1)
        _migrate_from_v4(db=v4_db)

    conn = sqlite3.connect(v4_db)
    row = conn.execute("SELECT id FROM bangumi WHERE name = 'TestAnime'").fetchone()
    conn.close()
    assert row[0] == "test"


def test_migrate_from_v4_without_keyword_column(tmp_path):
    db_path = tmp_path / "bangumi.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE bangumi (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            subtitle_group TEXT NOT NULL DEFAULT '',
            update_time CHAR(5) NOT NULL DEFAULT 'Unknown',
            cover TEXT NOT NULL DEFAULT '',
            status INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE followed (
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
        );
        CREATE TABLE download (
            id INTEGER PRIMARY KEY NOT NULL,
            bangumi_name TEXT NOT NULL,
            title TEXT NOT NULL,
            episode INTEGER NOT NULL,
            download TEXT NOT NULL,
            status INTEGER NOT NULL,
            task_id TEXT
        );

        INSERT INTO bangumi (id, name, subtitle_group, update_time, cover, status)
        VALUES (1, 'NoKeywordAnime', '[]', 'Mon', '', 0);
        """
    )
    conn.close()

    with mock.patch.object(cfg, "save_path", tmp_path / "save"), mock.patch("bgmi.lib.fetch.website"):
        _migrate_from_v4(db=db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT id, name FROM bangumi").fetchone()
    conn.close()
    assert row == ("1", "NoKeywordAnime")


def test_find_source_id_mismatches_compares_fetched_source_ids(tmp_path):
    db_path = tmp_path / "bangumi.db"
    conn = create_v5_db(db_path)
    conn.execute("INSERT INTO bangumi (id, name) VALUES ('123', 'NumericIdAnime')")
    conn.execute("INSERT INTO bangumi (id, name) VALUES ('same-id', 'SameIdAnime')")
    conn.commit()
    conn.close()

    mismatches = _find_source_id_mismatches(
        [
            WebsiteBangumi(id="123", name="NumericIdAnime"),
            WebsiteBangumi(id="same-id", name="SameIdAnime"),
            WebsiteBangumi(id="ignored", name="NotInDatabase"),
        ],
        db_path,
    )
    assert mismatches == []

    mismatches = _find_source_id_mismatches(
        [
            WebsiteBangumi(id="source-id", name="NumericIdAnime"),
            WebsiteBangumi(id="same-id", name="SameIdAnime"),
        ],
        db_path,
    )
    assert mismatches == [("NumericIdAnime", "123", "source-id")]


def test_update_database_does_not_refresh_matching_numeric_ids(tmp_path):
    db_path = tmp_path / "bangumi.db"
    old_file = tmp_path / "old"
    conn = create_v5_db(db_path)
    conn.execute("INSERT INTO bangumi (id, name) VALUES ('123', 'NumericIdAnime')")
    conn.commit()
    conn.close()
    old_file.write_text("5.0.0a3")

    with (
        mock.patch.object(cfg, "db_path", db_path),
        mock.patch("bgmi.lib.update.old_version_file", old_file),
        mock.patch("bgmi.lib.fetch.website") as website,
    ):
        website.fetch_bangumi_calendar.return_value = [WebsiteBangumi(id="123", name="NumericIdAnime")]
        update_database()

    website.fetch_bangumi_calendar.assert_called_once_with()
    website.fetch.assert_not_called()
    assert old_file.read_text() == __version__


def test_update_database_refreshes_mismatched_source_ids_once(tmp_path):
    db_path = tmp_path / "bangumi.db"
    old_file = tmp_path / "old"
    conn = create_v5_db(db_path)
    conn.execute("INSERT INTO bangumi (id, name) VALUES ('1', 'LegacyAnime')")
    conn.commit()
    conn.close()
    old_file.write_text("5.0.0a3")

    with (
        mock.patch.object(cfg, "db_path", db_path),
        mock.patch("bgmi.lib.update.old_version_file", old_file),
        mock.patch("bgmi.lib.fetch.website") as website,
    ):
        website.fetch_bangumi_calendar.return_value = [WebsiteBangumi(id="source-id", name="LegacyAnime")]
        update_database()
        update_database()

    website.fetch_bangumi_calendar.assert_called_once_with()
    website.fetch.assert_called_once_with(group_by_weekday=False)


def test_update_database_v4_migration_skips_legacy_id_check(v4_db, tmp_path):
    old_file = tmp_path / "old"
    old_file.write_text("4.5.1")

    with (
        mock.patch.object(cfg, "db_path", v4_db),
        mock.patch.object(cfg, "save_path", tmp_path / "save"),
        mock.patch("bgmi.lib.update.old_version_file", old_file),
        mock.patch("bgmi.lib.fetch.website") as website,
    ):
        update_database()

    website.fetch.assert_called_once_with(group_by_weekday=False)
    website.fetch_bangumi_calendar.assert_not_called()
    assert old_file.read_text() == __version__


def test_migrate_from_v4_followed_table(v4_db, tmp_path):
    with mock.patch.object(cfg, "save_path", tmp_path / "save"), mock.patch("bgmi.lib.fetch.website"):
        (tmp_path / "save").mkdir(parents=True, exist_ok=True)
        _migrate_from_v4(db=v4_db)

    cols = _get_table_columns(v4_db, "followed")
    assert "episode" not in cols
    assert "episodes" in cols
    assert "subtitle" in cols
    assert "include" in cols

    conn = sqlite3.connect(v4_db)
    row = conn.execute("SELECT bangumi_name, episodes, subtitle, include, exclude, regex FROM followed").fetchone()
    conn.close()
    assert row[0] == "TestAnime"
    import json

    episodes = json.loads(row[1])
    assert episodes == [1, 2, 3, 4, 5]
    assert json.loads(row[2]) == ["sub1", "sub2"]
    assert json.loads(row[3]) == ["keyword1"]
    assert json.loads(row[4]) == ["bad"]
    assert row[5] == ".*720.*"


def test_migrate_from_v4_download_table(v4_db, tmp_path):
    with mock.patch.object(cfg, "save_path", tmp_path / "save"), mock.patch("bgmi.lib.fetch.website"):
        (tmp_path / "save").mkdir(parents=True, exist_ok=True)
        _migrate_from_v4(db=v4_db)

    cols = _get_table_columns(v4_db, "download")
    assert "name" not in cols
    assert "bangumi_name" in cols
    assert "task_id" in cols

    conn = sqlite3.connect(v4_db)
    row = conn.execute("SELECT bangumi_name, title, task_id FROM download").fetchone()
    conn.close()
    assert row[0] == "TestAnime"
    assert row[1] == "TestAnime EP01"


def test_migrate_from_v4_drops_filter_table(v4_db, tmp_path):
    with mock.patch.object(cfg, "save_path", tmp_path / "save"), mock.patch("bgmi.lib.fetch.website"):
        (tmp_path / "save").mkdir(parents=True, exist_ok=True)
        _migrate_from_v4(db=v4_db)

    conn = sqlite3.connect(v4_db)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    assert "filter" not in tables


def test_migrate_from_v4_renames_cover_dir(v4_db, tmp_path):
    save_path = tmp_path / "save"
    cover_dir = save_path / "cover"
    cover_dir.mkdir(parents=True)
    (cover_dir / "test.jpg").write_text("fake image")

    with mock.patch.object(cfg, "save_path", save_path), mock.patch("bgmi.lib.fetch.website"):
        _migrate_from_v4(db=v4_db)

    assert not cover_dir.exists()
    assert (save_path / ".cover").is_dir()
    assert (save_path / ".cover" / "test.jpg").read_text() == "fake image"


def test_migrate_from_v4_cover_dir_already_exists(v4_db, tmp_path):
    save_path = tmp_path / "save"
    old_cover = save_path / "cover"
    new_cover = save_path / ".cover"
    old_cover.mkdir(parents=True)
    new_cover.mkdir(parents=True)
    (old_cover / "old.jpg").write_text("old")
    (new_cover / "new.jpg").write_text("new")

    with mock.patch.object(cfg, "save_path", save_path), mock.patch("bgmi.lib.fetch.website"):
        _migrate_from_v4(db=v4_db)

    # Should not overwrite existing .cover
    assert old_cover.exists()
    assert (new_cover / "new.jpg").read_text() == "new"


def test_scripts_table_migration(scripts_db_missing_cols):
    db_path = scripts_db_missing_cols

    cols_before = _get_table_columns(db_path, "scripts")
    assert "episodes" not in cols_before

    from bgmi.lib.update import exec_sql as _orig_exec_sql

    def exec_sql_with_db(sql, db=db_path):
        _orig_exec_sql(sql, db=db)

    with (
        mock.patch.object(cfg, "db_path", db_path),
        mock.patch("bgmi.lib.update.old_version_file", db_path.parent / "old"),
        mock.patch("bgmi.lib.update.exec_sql", exec_sql_with_db),
        mock.patch("bgmi.lib.fetch.website") as website,
    ):
        website.fetch_bangumi_calendar.return_value = []
        (db_path.parent / "old").write_text("5.0.0a3")
        update_database()

    cols_after = _get_table_columns(db_path, "scripts")
    assert "episodes" in cols_after
    assert "updated_time" in cols_after
    assert "update_day" in cols_after
    assert "cover" in cols_after

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT bangumi_name, episodes, updated_time, update_day, cover FROM scripts").fetchone()
    conn.close()
    assert row[0] == "ScriptAnime"
    assert row[1] == "[]"
    assert row[2] == 0
    assert row[3] == "Unknown"
    assert row[4] == ""
