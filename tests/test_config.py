from bgmi.config import BGMI_PATH, Config
from unittest.mock import patch


def test_default_log_path_uses_log_directory():
    cfg = Config()

    assert cfg.log_path == BGMI_PATH / "log"


def test_config_save_with_none_values(tmp_path):
    cfg = Config()
    config_file = tmp_path / "config.toml"
    with patch("bgmi.config.CONFIG_FILE_PATH", config_file):
        cfg.save()
        assert config_file.exists()
        content = config_file.read_text(encoding="utf8")
        assert len(content) > 0
