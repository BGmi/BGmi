import pytest

UBUNTU_INFO_HASH = "a1dfefec1a9dd7fa8a041ebeeea271db55126d2f"


@pytest.fixture()
def torrent_url():
    return f"magnet:?xt=urn:btih:{UBUNTU_INFO_HASH}&dn=ubuntu-24.04.3-live-server-amd64.iso&tr=udp://tracker.opentrackr.org:1337/announce"


@pytest.fixture()
def info_hash():
    return UBUNTU_INFO_HASH
