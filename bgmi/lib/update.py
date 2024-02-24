import sqlite3
from pathlib import Path

from packaging.version import Version, parse

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


def patch_db(start: Version, end: Version, db: Path = cfg.db_path) -> None:
    """
    Update db by order of versions
    """
    sql_path = Path("bgmi/lib/sql/")
    for filename in sorted(sql_path.glob("*.sql")):
        version = Version(filename.stem)
        if start < version <= end:
            with open(filename, encoding="utf8") as f:
                exec_sql(f.read(), db=db)


def update_database() -> None:
    if not old_version_file.exists():
        old_version_file.write_text(__version__, encoding="utf8")
        return

    previous = parse(old_version_file.read_text(encoding="utf8").strip())
    if previous < Version("5.0.0a0"):
        print_error(
            (
                "can't automatically upgrade from <5.0.0 version, "
                + " please backup your .bgmi files, remove them and use `bgmi install`\n"
                + RED
                + "All Data will lost, you will need to re-add your bangumi after re-install"
                + COLOR_END
            ),
            stop=True,
        )

    # try to patch database
    patch_db(start=previous, end=Version(__version__))
    # all upgrade done, write current version
    old_version_file.write_text(__version__, encoding="utf8")
