import atexit
import os
import pickle

import requests
from requests.adapters import HTTPAdapter, Retry

from bgmi.config import TMP_PATH

session = requests.Session()

retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
session.mount("https://mikanani.me/", HTTPAdapter(max_retries=retries))

mikan_cookies_path = os.path.join(TMP_PATH, "mikan_cookies.txt")

if os.path.exists(mikan_cookies_path):
    with open(mikan_cookies_path, "rb") as f:
        session.cookies.update(pickle.load(f))


@atexit.register
def save_cookies() -> None:
    with open(mikan_cookies_path, "wb") as f:
        pickle.dump(session.cookies, f)
