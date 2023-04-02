import os
import sqlite3
from pathlib import Path

from bgmi import __version__
from bgmi.config import BGMI_PATH, cfg
from bgmi.utils import print_error, print_info

OLD = BGMI_PATH.joinpath("old")


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
    if not os.path.exists(OLD):
        with open(OLD, "w", encoding="utf8") as f:
            f.write(__version__)
    else:
        with open(OLD, "r+", encoding="utf8") as f:
            f.read()
            f.seek(0)
            f.write(__version__)

    # if v < "1.0.25":
    #     pass
