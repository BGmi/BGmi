import requests
from requests.adapters import HTTPAdapter, Retry

session = requests.Session()

retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
session.mount("https://mikanani.me/", HTTPAdapter(max_retries=retries))
