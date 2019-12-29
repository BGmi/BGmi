from bgmi.downloader.base import ConnectError
from bgmi.downloader.deluge import DelugeRPC


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.

    session start

    """
    print('conftest for downloader')
    try:
        from bgmi.config import config_obj
        deluge = DelugeRPC(config_obj)
        res = deluge._call('web.get_hosts', [])
        host_id = res['result'][0][0]
        deluge._call('web.connect', [host_id])
    except ConnectError:
        pass
