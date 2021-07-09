import pytest


@pytest.fixture()
def torrent_url():
    return (
        "https://releases.ubuntu.com/21.04/"
        "ubuntu-21.04-live-server-amd64.iso.torrent"
    )
