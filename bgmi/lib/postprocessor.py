"""Post-download processor: move completed downloads to formatted paths."""

import shutil
from pathlib import Path
from typing import List

from loguru import logger

from bgmi.config import cfg
from bgmi.lib.download import get_download_driver
from bgmi.lib.season import strip_season_suffix
from bgmi.lib.table import Download, Followed
from bgmi.plugin.download import DownloadStatus
from bgmi.utils import normalize_path, print_error, print_info, print_success

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".flv", ".rmvb", ".mov", ".ts"}


def format_path(
    bangumi_name: str,
    season: int,
    episode: int,
    suffix: str,
    title: str,
) -> Path:
    """Apply the path formatter template and return the target path."""
    formatted = cfg.path_formatter.format(
        name=normalize_path(bangumi_name),
        season=season,
        episode=episode,
        suffix=suffix,
        title=title,
    )
    return cfg.save_path / formatted


def _pick_video_file(files: List[str]) -> str | None:
    """Pick the first video file from the list. Falls back to first file if no video found."""
    for f in files:
        if Path(f).suffix.lower() in VIDEO_EXTENSIONS:
            return f
    return files[0] if files else None


def move_to_formatted_path(dl: Download, files: List[str]) -> bool:
    """Move the first video file to formatter-determined location.

    Returns True if move succeeded, False otherwise.
    """
    try:
        followed = Followed.get(Followed.bangumi_name == dl.bangumi_name)
        season = followed.season
        episode_offset = followed.episode_offset
        name = followed.display_name or strip_season_suffix(dl.bangumi_name)
    except Followed.NotFoundError:
        season = 1
        episode_offset = 0
        name = strip_season_suffix(dl.bangumi_name)

    target_file = _pick_video_file(files)
    if not target_file:
        return False

    src = Path(target_file)
    if not src.exists():
        logger.warning("File not found, skipping: {}", target_file)
        return False

    suffix = src.suffix.lstrip(".")
    target = format_path(
        bangumi_name=name,
        season=season,
        episode=dl.episode + episode_offset,
        suffix=suffix,
        title=dl.title,
    )
    target.parent.mkdir(parents=True, exist_ok=True)

    print_success(f"Moving {src} -> {target}")
    shutil.move(str(src), str(target))
    return True


def _cleanup_download_dir(files: List[str]) -> None:
    """Remove the .downloads/<uuid>/ directory after successful move."""
    if not files:
        return
    src_dir = Path(files[0]).parent
    if src_dir.exists():
        shutil.rmtree(src_dir, ignore_errors=True)


def process_completed_downloads() -> None:
    """Check all DOWNLOADING tasks, move completed ones to formatted paths."""
    if not cfg.enable_path_formatter:
        return

    driver = get_download_driver(cfg.download_delegate)
    downloads = Download.get_all_downloads(status=Download.STATUS_DOWNLOADING)

    for dl in downloads:
        if not dl.task_id:
            continue

        try:
            status = driver.get_status(dl.task_id)
        except Exception as e:
            logger.warning("Failed to get status for task {}: {}", dl.task_id, e)
            continue

        if status == DownloadStatus.done:
            print_info(f"Download complete: {dl.title}")
            try:
                files = driver.get_files(dl.task_id)
                if not files:
                    logger.warning("No files found for completed task {}, will retry", dl.task_id)
                    continue

                if not move_to_formatted_path(dl, files):
                    logger.warning("Move failed for {}, will retry", dl.title)
                    continue

                _cleanup_download_dir(files)

                try:
                    driver.remove_download(dl.task_id)
                except Exception as e:
                    logger.warning("Failed to remove task {} from downloader: {}", dl.task_id, e)

                dl.downloaded()
            except Exception as e:
                print_error(f"Failed to post-process {dl.title}: {e}", stop=False)
                logger.exception("Post-processing error for {}", dl.title)

        elif status == DownloadStatus.error:
            logger.error("Download failed: {}", dl.title)
            dl.status = Download.STATUS_NOT_DOWNLOAD
            dl.save()
