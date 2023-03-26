import atexit
import pathlib
import pickle

import requests
from requests.adapters import HTTPAdapter, Retry

from bgmi.config import cfg

session = requests.Session()

retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
session.mount("https://mikanani.me/", HTTPAdapter(max_retries=retries))

cookies_file = pathlib.Path(cfg.tmp_path).joinpath("mikan_cookies.txt")

if cookies_file.exists():
    with cookies_file.open("rb") as f:
        data = {}
        try:
            data = pickle.load(f)
        except pickle.UnpicklingError:
            pass
        session.cookies.update(data)


@atexit.register
def save_cookies() -> None:
    with open(cookies_file, "wb") as f:
        pickle.dump(session.cookies, f)
