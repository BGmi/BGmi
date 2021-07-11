from bgmi.lib.models import Filter
from bgmi.website.model import Episode


def test_include():
    e = Filter(include="2,3,5").apply_on_episodes(
        [
            Episode(name="1", title="1", download="1", episode=1),
            Episode(name="1", title="1", download="2", episode=1),
            Episode(name="2", title="2", download="3", episode=2),
            Episode(name="2", title="2", download="4", episode=2),
            Episode(name="3", title="3", download="5", episode=3),
            Episode(name="5", title="5", download="6", episode=5),
        ]
    )
    assert len(e) == 4, e
    assert {x.download for x in e} == set("3456")


def test_exclude():
    e = Filter(exclude="2,3,5").apply_on_episodes(
        [
            Episode(title="1", download="1", episode=1),
            Episode(title="1", download="2", episode=2),
            Episode(title="2", download="3", episode=1),
            Episode(title="2", download="4", episode=2),
            Episode(title="3", download="5", episode=3),
            Episode(title="5", download="6", episode=5),
        ]
    )
    assert len(e) == 2, e
    assert {x.download for x in e} == {"1", "2"}
