import sqlite3
from pathlib import Path

import semver

from bgmi import __version__
from bgmi.config import BGMI_PATH, cfg
from bgmi.utils import COLOR_END, RED, print_error, print_info

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


def update_database() -> None:
    if not old_version_file.exists():
        old_version_file.write_text(__version__, encoding="utf8")
        return

    previous = semver.VersionInfo.parse(old_version_file.read_text(encoding="utf8"))
    if previous < semver.VersionInfo(major=4):
        print_error(
            (
                "can't automatically upgrade from <4.0.0 version, "
                + " please backup your .bgmi files, remove them and use `bgmi install`\n"
                + RED
                + "All Data will lost, you will need to re-add your bangumi after re-install"
                + COLOR_END
            ),
            stop=True,
        )

    # all upgrade done, write current version
    old_version_file.write_text(__version__, encoding="utf8")
