import pytest

from bgmi.lib.models import Followed, recreate_source_relatively_table
from bgmi.main import main


@pytest.fixture()
def bangumi_names(data_source_bangumi_name):
    return data_source_bangumi_name["bangumi_moe"]


@pytest.fixture()
def clean_bgmi():
    recreate_source_relatively_table()
    yield
    recreate_source_relatively_table()


def test_gen_nginx_conf():
    main("gen nginx.conf --server-name _".split())


def test_cal_force_update():
    main("cal -f".split())


def test_cal_config():
    main("config".split())
    main("config ADMIN_TOKEN 233".split())
    main("config DOWNLOAD_DELEGATE xunlei".split())
    main("config BANGUMI_MOE_URL https://bangumi.moe".split())


def test_add(bangumi_names, clean_bgmi):
    main("add {} {} {}".format(*bangumi_names).split())


def test_update(bangumi_names, clean_bgmi):
    main("add {} {} {}".format(*bangumi_names).split())
    main(["update"])


def test_update_single(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main("add {}".format(name).split())
    main(["update", name])


def test_search(bangumi_names, clean_bgmi):
    main(["search", "海贼王", "--regex-filter", ".*MP4.*720P.*"])


def test_delete(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main("add {} --episode 0".format(name).split())
    main("delete --name {}".format(name).split())


def test_delete_batch(bangumi_names, clean_bgmi):
    main("add {} {} {} --episode 0".format(*bangumi_names).split())
    main("delete  --clear-all --batch".split())


def test_filter(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main("add {} --episode 0".format(name).split())
    main(["filter", name, "--subtitle", "", "--exclude", "MKV", "--regex", "720p|720P"])


def test_fetch(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main("add {} --episode 0".format(name).split())
    main("fetch {}".format(name).split())


def test_mark(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main("add {} --episode 0".format(name).split())
    main("mark {} 1".format(name).split())
    assert Followed.get(bangumi_name=name).episode == 1
