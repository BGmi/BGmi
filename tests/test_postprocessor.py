"""Tests for season parsing, formatter, and postprocessor."""

import tempfile
from pathlib import Path
from unittest import mock

from bgmi.lib.season import parse_season, strip_season_suffix


class TestParseSeason:
    def test_chinese_digit(self):
        assert parse_season("进击的巨人 第二季") == 2
        assert parse_season("某某某 第十二季") == 12
        assert parse_season("某某某 第三季") == 3
        assert parse_season("王者天下 第二十一季") == 21
        assert parse_season("银河英雄传说 第三十二季") == 32

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
        assert parse_season("PSYCHO-PASS") == 1


class TestStripSeasonSuffix:
    def test_chinese_season_suffix(self):
        assert strip_season_suffix("相反的你和我 第二季") == "相反的你和我"
        assert strip_season_suffix("进击的巨人 第2季") == "进击的巨人"

    def test_english_season_suffix(self):
        assert strip_season_suffix("Attack on Titan Season 3") == "Attack on Titan"
        assert strip_season_suffix("Title S02") == "Title"

    def test_keeps_non_suffix_text(self):
        assert strip_season_suffix("PSYCHO-PASS") == "PSYCHO-PASS"
        assert strip_season_suffix("名侦探柯南") == "名侦探柯南"


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


class TestPickVideoFile:
    def test_picks_first_video(self):
        from bgmi.lib.postprocessor import _pick_video_file

        files = ["/tmp/sub.ass", "/tmp/ep01.mp4", "/tmp/ep02.mkv"]
        assert _pick_video_file(files) == "/tmp/ep01.mp4"

    def test_fallback_to_first_file(self):
        from bgmi.lib.postprocessor import _pick_video_file

        files = ["/tmp/readme.txt", "/tmp/data.nfo"]
        assert _pick_video_file(files) == "/tmp/readme.txt"

    def test_empty_list(self):
        from bgmi.lib.postprocessor import _pick_video_file

        assert _pick_video_file([]) is None


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
                mock_followed_obj.episode_offset = 0
                mock_followed_obj.display_name = ""
                mock_followed.get.return_value = mock_followed_obj

                result = move_to_formatted_path(dl, [str(src_file)])

                assert result is True
                expected = dst_dir / "TestBangumi" / "S02" / "E03.mp4"
                assert expected.exists()
                assert expected.read_text() == "video content"

    def test_strips_season_suffix_from_default_name(self):
        from bgmi.lib.postprocessor import move_to_formatted_path
        from bgmi.lib.table import Download

        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            src_file = src_dir / "episode.mp4"
            src_file.write_text("video content")

            dst_dir = Path(tmpdir) / "dst"

            dl = mock.Mock(spec=Download)
            dl.bangumi_name = "相反的你和我 第二季"
            dl.episode = 1
            dl.title = "Episode 01"

            with (
                mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
                mock.patch("bgmi.lib.postprocessor.Followed") as mock_followed,
            ):
                mock_cfg.save_path = dst_dir
                mock_cfg.path_formatter = "{name}/S{season:02d}/E{episode:02d}.{suffix}"

                mock_followed_obj = mock.Mock()
                mock_followed_obj.season = 2
                mock_followed_obj.episode_offset = 0
                mock_followed_obj.display_name = ""
                mock_followed.get.return_value = mock_followed_obj

                result = move_to_formatted_path(dl, [str(src_file)])

                assert result is True
                expected = dst_dir / "相反的你和我" / "S02" / "E01.mp4"
                assert expected.exists()

    def test_display_name_overrides_season_suffix_stripping(self):
        from bgmi.lib.postprocessor import move_to_formatted_path
        from bgmi.lib.table import Download

        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            src_file = src_dir / "episode.mp4"
            src_file.write_text("video content")

            dst_dir = Path(tmpdir) / "dst"

            dl = mock.Mock(spec=Download)
            dl.bangumi_name = "相反的你和我 第二季"
            dl.episode = 1
            dl.title = "Episode 01"

            with (
                mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
                mock.patch("bgmi.lib.postprocessor.Followed") as mock_followed,
            ):
                mock_cfg.save_path = dst_dir
                mock_cfg.path_formatter = "{name}/S{season:02d}/E{episode:02d}.{suffix}"

                mock_followed_obj = mock.Mock()
                mock_followed_obj.season = 2
                mock_followed_obj.episode_offset = 0
                mock_followed_obj.display_name = "You and I Are Polar Opposites"
                mock_followed.get.return_value = mock_followed_obj

                result = move_to_formatted_path(dl, [str(src_file)])

                assert result is True
                expected = dst_dir / "You and I Are Polar Opposites" / "S02" / "E01.mp4"
                assert expected.exists()

    def test_picks_first_video_from_multiple(self):
        from bgmi.lib.postprocessor import move_to_formatted_path
        from bgmi.lib.table import Download

        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            sub_file = src_dir / "sub.ass"
            sub_file.write_text("subtitle")
            vid1 = src_dir / "ep_720p.mp4"
            vid1.write_text("video 720")
            vid2 = src_dir / "ep_1080p.mp4"
            vid2.write_text("video 1080")

            dst_dir = Path(tmpdir) / "dst"

            dl = mock.Mock(spec=Download)
            dl.bangumi_name = "Anime"
            dl.episode = 1
            dl.title = "EP01"

            with (
                mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
                mock.patch("bgmi.lib.postprocessor.Followed") as mock_followed,
            ):
                mock_cfg.save_path = dst_dir
                mock_cfg.path_formatter = "{name}/S{season:02d}/E{episode:02d}.{suffix}"

                mock_followed_obj = mock.Mock()
                mock_followed_obj.season = 1
                mock_followed_obj.episode_offset = 0
                mock_followed_obj.display_name = ""
                mock_followed.get.return_value = mock_followed_obj

                result = move_to_formatted_path(dl, [str(sub_file), str(vid1), str(vid2)])

                assert result is True
                expected = dst_dir / "Anime" / "S01" / "E01.mp4"
                assert expected.exists()
                assert expected.read_text() == "video 720"

    def test_returns_false_for_missing_file(self):
        from bgmi.lib.postprocessor import move_to_formatted_path
        from bgmi.lib.table import Download

        dl = mock.Mock(spec=Download)
        dl.bangumi_name = "Test"
        dl.episode = 1
        dl.title = "T"

        with (
            mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
            mock.patch("bgmi.lib.postprocessor.Followed") as mock_followed,
        ):
            mock_cfg.save_path = Path("/tmp/dst")
            mock_cfg.path_formatter = "{name}/E{episode:02d}.{suffix}"
            mock_followed_obj = mock.Mock()
            mock_followed_obj.season = 1
            mock_followed.get.return_value = mock_followed_obj

            result = move_to_formatted_path(dl, ["/nonexistent/file.mp4"])
            assert result is False

    def test_returns_false_for_empty_files(self):
        from bgmi.lib.postprocessor import move_to_formatted_path
        from bgmi.lib.table import Download

        dl = mock.Mock(spec=Download)
        dl.bangumi_name = "Test"
        dl.episode = 1
        dl.title = "T"

        with (
            mock.patch("bgmi.lib.postprocessor.cfg"),
            mock.patch("bgmi.lib.postprocessor.Followed") as mock_followed,
        ):
            mock_followed_obj = mock.Mock()
            mock_followed_obj.season = 1
            mock_followed.get.return_value = mock_followed_obj

            result = move_to_formatted_path(dl, [])
            assert result is False


class TestCleanupDownloadDir:
    def test_removes_directory(self):
        from bgmi.lib.postprocessor import _cleanup_download_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            dl_dir = Path(tmpdir) / ".downloads" / "uuid-123"
            dl_dir.mkdir(parents=True)
            f = dl_dir / "file.mp4"
            f.write_text("data")

            _cleanup_download_dir([str(f)])

            assert not dl_dir.exists()

    def test_handles_empty_list(self):
        from bgmi.lib.postprocessor import _cleanup_download_dir

        _cleanup_download_dir([])


class TestProcessCompletedDownloads:
    def test_skips_when_formatter_disabled(self):
        from bgmi.lib.postprocessor import process_completed_downloads

        with mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg:
            mock_cfg.enable_path_formatter = False
            with mock.patch("bgmi.lib.postprocessor.get_download_driver") as mock_driver:
                process_completed_downloads()
                mock_driver.assert_not_called()

    def test_processes_done_task(self):
        from bgmi.lib.postprocessor import process_completed_downloads
        from bgmi.plugin.download import DownloadStatus

        mock_dl = mock.Mock()
        mock_dl.task_id = "abc123"
        mock_dl.bangumi_name = "Test"
        mock_dl.episode = 1
        mock_dl.title = "Ep01"

        mock_driver = mock.Mock()
        mock_driver.get_status.return_value = DownloadStatus.done
        mock_driver.get_files.return_value = ["/tmp/test.mp4"]

        with (
            mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
            mock.patch("bgmi.lib.postprocessor.get_download_driver", return_value=mock_driver),
            mock.patch("bgmi.lib.postprocessor.Download") as mock_download_cls,
            mock.patch("bgmi.lib.postprocessor.move_to_formatted_path", return_value=True),
            mock.patch("bgmi.lib.postprocessor._cleanup_download_dir"),
        ):
            mock_cfg.enable_path_formatter = True
            mock_cfg.download_delegate = "aria2-rpc"
            mock_download_cls.STATUS_DOWNLOADING = 1
            mock_download_cls.get_all_downloads.return_value = [mock_dl]

            process_completed_downloads()

            mock_driver.get_status.assert_called_once_with("abc123")
            mock_driver.get_files.assert_called_once_with("abc123")
            mock_driver.remove_download.assert_called_once_with("abc123")
            mock_dl.downloaded.assert_called_once()

    def test_skips_empty_files(self):
        from bgmi.lib.postprocessor import process_completed_downloads
        from bgmi.plugin.download import DownloadStatus

        mock_dl = mock.Mock()
        mock_dl.task_id = "abc123"
        mock_dl.bangumi_name = "Test"
        mock_dl.episode = 1
        mock_dl.title = "Ep01"

        mock_driver = mock.Mock()
        mock_driver.get_status.return_value = DownloadStatus.done
        mock_driver.get_files.return_value = []

        with (
            mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
            mock.patch("bgmi.lib.postprocessor.get_download_driver", return_value=mock_driver),
            mock.patch("bgmi.lib.postprocessor.Download") as mock_download_cls,
        ):
            mock_cfg.enable_path_formatter = True
            mock_cfg.download_delegate = "aria2-rpc"
            mock_download_cls.STATUS_DOWNLOADING = 1
            mock_download_cls.get_all_downloads.return_value = [mock_dl]

            process_completed_downloads()

            mock_dl.downloaded.assert_not_called()

    def test_marks_error_as_not_download(self):
        from bgmi.lib.postprocessor import process_completed_downloads
        from bgmi.plugin.download import DownloadStatus

        mock_dl = mock.Mock()
        mock_dl.task_id = "abc123"
        mock_dl.bangumi_name = "Test"
        mock_dl.episode = 1
        mock_dl.title = "Ep01"
        mock_dl.STATUS_NOT_DOWNLOAD = 0

        mock_driver = mock.Mock()
        mock_driver.get_status.return_value = DownloadStatus.error

        with (
            mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
            mock.patch("bgmi.lib.postprocessor.get_download_driver", return_value=mock_driver),
            mock.patch("bgmi.lib.postprocessor.Download") as mock_download_cls,
        ):
            mock_cfg.enable_path_formatter = True
            mock_cfg.download_delegate = "aria2-rpc"
            mock_download_cls.STATUS_DOWNLOADING = 1
            mock_download_cls.STATUS_NOT_DOWNLOAD = 0
            mock_download_cls.get_all_downloads.return_value = [mock_dl]

            process_completed_downloads()

            assert mock_dl.status == 0
            mock_dl.save.assert_called_once()

    def test_skips_downloading_task(self):
        from bgmi.lib.postprocessor import process_completed_downloads
        from bgmi.plugin.download import DownloadStatus

        mock_dl = mock.Mock()
        mock_dl.task_id = "abc123"

        mock_driver = mock.Mock()
        mock_driver.get_status.return_value = DownloadStatus.downloading

        with (
            mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
            mock.patch("bgmi.lib.postprocessor.get_download_driver", return_value=mock_driver),
            mock.patch("bgmi.lib.postprocessor.Download") as mock_download_cls,
        ):
            mock_cfg.enable_path_formatter = True
            mock_cfg.download_delegate = "aria2-rpc"
            mock_download_cls.STATUS_DOWNLOADING = 1
            mock_download_cls.get_all_downloads.return_value = [mock_dl]

            process_completed_downloads()

            mock_dl.downloaded.assert_not_called()
            mock_dl.save.assert_not_called()

    def test_continues_on_status_check_failure(self):
        from bgmi.lib.postprocessor import process_completed_downloads

        mock_dl = mock.Mock()
        mock_dl.task_id = "abc123"

        mock_driver = mock.Mock()
        mock_driver.get_status.side_effect = ConnectionError("timeout")

        with (
            mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
            mock.patch("bgmi.lib.postprocessor.get_download_driver", return_value=mock_driver),
            mock.patch("bgmi.lib.postprocessor.Download") as mock_download_cls,
        ):
            mock_cfg.enable_path_formatter = True
            mock_cfg.download_delegate = "aria2-rpc"
            mock_download_cls.STATUS_DOWNLOADING = 1
            mock_download_cls.get_all_downloads.return_value = [mock_dl]

            process_completed_downloads()

            mock_dl.downloaded.assert_not_called()

    def test_remove_download_failure_does_not_block(self):
        from bgmi.lib.postprocessor import process_completed_downloads
        from bgmi.plugin.download import DownloadStatus

        mock_dl = mock.Mock()
        mock_dl.task_id = "abc123"
        mock_dl.bangumi_name = "Test"
        mock_dl.episode = 1
        mock_dl.title = "Ep01"

        mock_driver = mock.Mock()
        mock_driver.get_status.return_value = DownloadStatus.done
        mock_driver.get_files.return_value = ["/tmp/test.mp4"]
        mock_driver.remove_download.side_effect = Exception("RPC error")

        with (
            mock.patch("bgmi.lib.postprocessor.cfg") as mock_cfg,
            mock.patch("bgmi.lib.postprocessor.get_download_driver", return_value=mock_driver),
            mock.patch("bgmi.lib.postprocessor.Download") as mock_download_cls,
            mock.patch("bgmi.lib.postprocessor.move_to_formatted_path", return_value=True),
            mock.patch("bgmi.lib.postprocessor._cleanup_download_dir"),
        ):
            mock_cfg.enable_path_formatter = True
            mock_cfg.download_delegate = "aria2-rpc"
            mock_download_cls.STATUS_DOWNLOADING = 1
            mock_download_cls.get_all_downloads.return_value = [mock_dl]

            process_completed_downloads()

            mock_dl.downloaded.assert_called_once()
