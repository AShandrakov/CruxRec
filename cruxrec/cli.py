import argparse
import logging

from utils import setup_logging
from pipline import Pipline


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

    pipline = Pipline(args.prompt, args.url, args.lang)
    print(pipline.start())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    main()
