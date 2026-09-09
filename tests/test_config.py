import pytest

from bgmi.config import BGMI_PATH, Config
from bgmi.main import config_get


def test_default_log_path_uses_log_directory():
    cfg = Config()

    assert cfg.log_path == BGMI_PATH / "log"


def test_config_get_reads_nested_value(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[http]\nadmin_token = "river-stone-42"\n', encoding="utf-8")
    monkeypatch.setattr("bgmi.main.CONFIG_FILE_PATH", config_path)

    with pytest.raises(SystemExit) as exc_info:
        config_get(["http", "admin_token"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "config http.admin_token river-stone-42\n"


def test_config_get_handles_path_below_scalar(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "config.toml"
    config_path.write_text("max_path = 4\n", encoding="utf-8")
    monkeypatch.setattr("bgmi.main.CONFIG_FILE_PATH", config_path)

    with pytest.raises(SystemExit) as exc_info:
        config_get(["max_path", "label"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "config max_path.label {}\n"
