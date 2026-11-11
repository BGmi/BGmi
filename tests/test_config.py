import pytest
from pydantic import ValidationError

from bgmi.config import BGMI_PATH, Config


def test_default_log_path_uses_log_directory():
    cfg = Config()

    assert cfg.log_path == BGMI_PATH / "log"


def test_mikan_url_rejects_invalid_url():
    with pytest.raises(ValidationError):
        Config(mikan_url="not-a-url")
