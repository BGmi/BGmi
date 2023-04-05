import atexit
import pathlib
import pickle

import requests
from requests.adapters import HTTPAdapter, Retry

from bgmi.config import cfg

session = requests.Session()

if cfg.proxy:
    session.proxies = {"http": cfg.proxy, "https": cfg.proxy}

retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
session.mount("https://mikanani.me/", HTTPAdapter(max_retries=retries))

cookies_file = pathlib.Path(cfg.tmp_path).joinpath("mikan_cookies.txt")

if cookies_file.exists():
    data = {}
    dump = cookies_file.read_bytes()
    try:
        data = pickle.loads(dump)
    except pickle.UnpicklingError:
        cookies_file.unlink()
    session.cookies.update(data)


@atexit.register
def save_cookies() -> None:
    if cookies_file.parent.exists() and cookies_file.parent.is_dir():
        cookies_file.write_bytes(pickle.dumps(session.cookies))
