from bgmi.config import BGMI_PATH, Config


def test_default_log_path_uses_log_directory():
    cfg = Config()

    assert cfg.log_path == BGMI_PATH / "log"
