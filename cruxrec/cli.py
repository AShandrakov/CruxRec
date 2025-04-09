import argparse
import logging
import sys
import os

from summarizer import GeminiSummarizer
from subs_provider import SubsProvider
from utils import setup_logging


def main() -> None:
    """
    CruxRec: CLI utility for extracting YouTube subtitles and summarizing them using Gemini.
    """
    parser = argparse.ArgumentParser(
        description="CruxRec: Extract YouTube subtitles and summarize them using Gemini."
    )
    parser.add_argument("prompt", help="Prompt ")
    parser.add_argument("url", help="URL of the YouTube video.")
    parser.add_argument(
        "--lang", default="ru", help="Subtitle language code (default: 'ru')."
    )
    parser.add_argument(
        "--auto-sub",
        action="store_true",
        help="Use auto-generated subtitles if official ones are not available.",
    )

    args = parser.parse_args()

    setup_logging()

    logger = logging.getLogger("cli")
    logger.info("Fetching subtitles...")
    subs_provider = SubsProvider()
    subs_provider.remove_subtitles()
    subtitles_text = subs_provider.fetch_subtitles(args.url, args.lang, args.auto_sub)

    if not subtitles_text:
        logger.warning(
            "Failed to retrieve subtitles. The video may not have any available."
        )
        sys.exit(1)

    logger.info("Preparing subtitles...")
    logger.debug("Sending subtitles for summarization...")

    key = os.environ["GEMINI_KEY"]
    try:
        summarizer = GeminiSummarizer(key, args.prompt)
        summary = summarizer.summarize(subtitles_text)
    except Exception as exp:
        logger.exception("Error occurred during summarization. {exp}")
        sys.exit(1)

    print(summary)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    main()
