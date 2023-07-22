import pytest

from bgmi.utils import normalize_path


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("https://example.com/ee", "https/example.com/ee"),
        ("q://s?*", "q/s"),
        ("/q://s?*", "q/s"),
    ],
)
def test_normalize_path(s: str, expected: str) -> None:
    assert normalize_path(s) == expected
