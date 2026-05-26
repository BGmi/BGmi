"""Post-download processor: move completed downloads to formatted paths."""

import shutil
from pathlib import Path
from typing import List

from loguru import logger

from bgmi.config import cfg
from bgmi.lib.download import get_download_driver
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


def move_to_formatted_path(dl: Download, files: List[str]) -> None:
    """Move downloaded files to formatter-determined locations."""
    try:
        followed = Followed.get(Followed.bangumi_name == dl.bangumi_name)
        season = followed.season
    except Followed.NotFoundError:
        season = 1

    video_files = [f for f in files if Path(f).suffix.lower() in VIDEO_EXTENSIONS]
    if not video_files:
        video_files = files

    for f in video_files:
        src = Path(f)
        if not src.exists():
            logger.warning("File not found, skipping: {}", f)
            continue

        suffix = src.suffix.lstrip(".")
        target = format_path(
            bangumi_name=dl.bangumi_name,
            season=season,
            episode=dl.episode,
            suffix=suffix,
            title=dl.title,
        )
        target.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Moving {} -> {}", src, target)
        shutil.move(str(src), str(target))
        print_success(f"Moved: {src.name} -> {target}")

    # Clean up empty download directory
    for f in files:
        src_dir = Path(f).parent
        if src_dir.exists() and not any(src_dir.iterdir()):
            src_dir.rmdir()
            if src_dir.parent.name == ".downloads" and not any(src_dir.parent.iterdir()):
                src_dir.parent.rmdir()


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
                if files:
                    move_to_formatted_path(dl, files)
                else:
                    logger.warning("No files found for completed task {}", dl.task_id)
                dl.downloaded()
            except Exception as e:
                print_error(f"Failed to post-process {dl.title}: {e}", stop=False)
                logger.exception("Post-processing error for {}", dl.title)
        elif status == DownloadStatus.error:
            logger.error("Download failed: {}", dl.title)
            dl.status = Download.STATUS_NOT_DOWNLOAD
            dl.save()
