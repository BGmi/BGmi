import pytest


@pytest.fixture()
def torrent_url():
    return "https://releases.ubuntu.com/21.04/ubuntu-21.04-live-server-amd64.iso.torrent"


@pytest.fixture()
def info_hash():
    return "cab507494d02ebb1178b38f2e9d7be299c86b862"
