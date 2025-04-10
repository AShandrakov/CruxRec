import logging
import re
from pathlib import Path
from typing import List, Optional

from yt_dlp import YoutubeDL

logger = logging.getLogger("services")


class SubsProvider:
    def find_subtitle_file(
        self,
        pattern: str = "subs.*",
        search_dir: Path = Path("."),
    ) -> Optional[Path]:
        resolved_dir = search_dir.resolve()
        logger.debug(f"Searching for subtitles in directory: {resolved_dir}")

        matched_files = list(resolved_dir.rglob(pattern))
        if not matched_files:
            logger.debug(f"No files matching pattern '{pattern}' were found.")
            return None

        logger.debug("Found the following subtitle files:")
        for file in matched_files:
            logger.debug(f" - {file}")
        return matched_files[0]

    def fetch_subtitles(
        self,
        url: str,
        lang: str = "ru",
        auto_sub: bool = False,
    ) -> str | None:
        outtmpl = "subs.%(ext)s"

        def download_subtitles(write_auto: bool) -> bool:
            ydl_opts = {
                "skip_download": True,
                "outtmpl": outtmpl,
                "writesub": not write_auto,
                "writeautomaticsub": write_auto,
                "subtitleslangs": [lang] if lang else None,
            }
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    logger.debug(
                        f"Starting subtitles download (auto={write_auto}), lang='{lang}'"
                    )
                    ydl.download([url])
                return True
            except Exception as exc:
                logger.warning("Error downloading subtitles", exc_info=exc)
                return False

        download_subtitles(auto_sub)

        sub_file = self.find_subtitle_file()
        if sub_file:
            file_size = sub_file.stat().st_size
            if file_size == 0:
                logger.debug(f"Subtitle file '{sub_file}' is empty (size=0). Ignoring.")
                sub_file = None

        if not sub_file and not auto_sub:
            logger.debug(
                "Official subtitles not found or empty, trying auto-generated subtitles..."
            )
            if not download_subtitles(True):
                logger.debug("Fallback download (auto-sub) failed.")
                return None
            sub_file = self.find_subtitle_file()
            if sub_file and sub_file.stat().st_size == 0:
                logger.debug("Fallback subtitle file is empty.")
                sub_file = None

        if not sub_file:
            logger.debug("Could not locate a valid downloaded subtitle file.")
            return None

        subtitles_text = self.parse_subtitle(str(sub_file))
        if not subtitles_text.strip():
            logger.debug("Parsed subtitles are empty.")
            return None

        return subtitles_text

    def parse_subtitle(self, subtitle_path: str) -> str:
        timestamp_re = re.compile(
            r"^\d{2}:\d{2}:\d{2}\.\d+\s*-->\s*\d{2}:\d{2}:\d{2}\.\d+"
        )
        html_tag_re = re.compile(r"<[^>]*>")
        try:
            with open(subtitle_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except IOError as e:
            raise IOError(f"Error reading file '{subtitle_path}': {e}")

        cleaned_lines: List[str] = []
        prev_line = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if (
                line.startswith("WEBVTT")
                or line.startswith("Kind:")
                or line.startswith("Language:")
            ):
                continue

            if timestamp_re.match(line):
                continue

            line = html_tag_re.sub("", line).strip()
            if not line:
                continue

            if line != prev_line:
                cleaned_lines.append(line)
                prev_line = line

        return "\n".join(cleaned_lines)

    def remove_subtitles(
        self,
        pattern: str = "subs.*",
        search_dir: Path = Path("."),
    ) -> None:
        resolved_dir = search_dir.resolve()
        deleted_files = 0
        for sub_file in resolved_dir.rglob(pattern):
            try:
                sub_file.unlink()
                logger.debug(f"Removed subtitle file: {sub_file}")
                deleted_files += 1
            except Exception as exc:
                logger.warning(
                    f"Failed to remove file '{sub_file}': {exc}", exc_info=exc
                )

        if deleted_files:
            logger.info(f"Removed {deleted_files} subtitle file(s).")
        else:
            logger.debug(f"No subtitle files found to remove with pattern '{pattern}'.")
