"""Tests for season parsing, formatter, and postprocessor."""

import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from bgmi.lib.season import parse_season


class TestParseSeason:
    def test_chinese_digit(self):
        assert parse_season("进击的巨人 第二季") == 2
        assert parse_season("某某某 第十二季") == 12
        assert parse_season("某某某 第三季") == 3

    def test_arabic_digit(self):
        assert parse_season("进击的巨人 第2季") == 2
        assert parse_season("名侦探柯南 第15季") == 15

    def test_english_season(self):
        assert parse_season("Attack on Titan Season 3") == 3
        assert parse_season("Attack on Titan season2") == 2

    def test_s_prefix(self):
        assert parse_season("Title S02") == 2
        assert parse_season("Title S3") == 3

    def test_ordinal_season(self):
        assert parse_season("Attack on Titan 2nd Season") == 2
        assert parse_season("Title 3rd season") == 3

    def test_no_season(self):
        assert parse_season("名侦探柯南") == 1
        assert parse_season("进击的巨人") == 1
        assert parse_season("") == 1

    def test_part(self):
        assert parse_season("某某某 Part 2") == 2

    def test_s_not_in_word(self):
        # "S" inside a word should not match
        assert parse_season("PSYCHO-PASS") == 1


class TestFormatPath:
    def test_basic_format(self):
        from bgmi.lib.postprocessor import format_path

        with mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg:
            mock_cfg.save_path = Path("/bangumi")
            mock_cfg.path_formatter = "{name}/S{season:02d}/E{episode:02d}.{suffix}"

            result = format_path(
                bangumi_name="名侦探柯南",
                season=1,
                episode=5,
                suffix="mp4",
                title="test title",
            )
            assert result == Path("/bangumi/名侦探柯南/S01/E05.mp4")

    def test_custom_format(self):
        from bgmi.lib.postprocessor import format_path

        with mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg:
            mock_cfg.save_path = Path("/data/anime")
            mock_cfg.path_formatter = "{name}/Season {season}/{title}.{suffix}"

            result = format_path(
                bangumi_name="进击的巨人",
                season=3,
                episode=1,
                suffix="mkv",
                title="Episode 01",
            )
            assert result == Path("/data/anime/进击的巨人/Season 3/Episode 01.mkv")


class TestMoveToFormattedPath:
    def test_move_video_file(self):
        from bgmi.lib.postprocessor import move_to_formatted_path
        from bgmi.lib.table import Download

        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            src_file = src_dir / "test_episode.mp4"
            src_file.write_text("video content")

            dst_dir = Path(tmpdir) / "dst"

            dl = mock.Mock(spec=Download)
            dl.bangumi_name = "TestBangumi"
            dl.episode = 3
            dl.title = "Test Episode"

            with (
                mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
                mock.patch("bgmi.lib.postprocessor.Followed") as mock_followed,
            ):
                mock_cfg.save_path = dst_dir
                mock_cfg.path_formatter = "{name}/S{season:02d}/E{episode:02d}.{suffix}"

                mock_followed_obj = mock.Mock()
                mock_followed_obj.season = 2
                mock_followed.get.return_value = mock_followed_obj

                move_to_formatted_path(dl, [str(src_file)])

                expected = dst_dir / "TestBangumi" / "S02" / "E03.mp4"
                assert expected.exists()
                assert expected.read_text() == "video content"
