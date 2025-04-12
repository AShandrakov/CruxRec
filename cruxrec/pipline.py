import logging
import os
import sys
from summarizer import GeminiSummarizer
from subs_provider import SubsProvider
from transcriber import Transcriber


class Pipline:
    def __init__(self, prompt: str, url: str, lang: str = "ru") -> None:
        self.prompt = prompt
        self.url = url
        self.lang = lang
        self.logger = logging.getLogger("services")

    def start(self) -> str | None:
        self.logger.debug("Pipline has been started")

        try:
            key = os.environ["GEMINI_KEY"]
        except KeyError:
            self.logger.error(
                "Error: Missing required local variable 'GEMINI_KEY'. Please set it before running the application."
            )
            sys.exit(1)

        subtitles_provider = SubsProvider()
        subtitles_text = subtitles_provider.fetch_subtitles(self.url, self.lang)

        if not subtitles_text:
            self.logger.warning(
                "Failed to retrieve subtitles. The video may not have any available."
            )
            try:
                openai_key = os.environ["OPENAI_API_KEY"]
            except KeyError:
                self.logger.error(
                    "Error: Missing required local variable 'OPENAI_API_KEY'. Please set it before running the application."
                )
                sys.exit(1)

            transcriber = Transcriber(openai_key)
            subtitles_text = transcriber.transcribe_from_url(self.url)

        if not subtitles_text:
            self.logger.error("Failed to transribe subtitles from video")
            return None

        try:
            summarizer = GeminiSummarizer(key, self.prompt)
            if isinstance(subtitles_text, str):
                summary = summarizer.summarize(subtitles_text)
                return summary
        except Exception:
            self.logger.exception("Error occurred during summarization.")
            return None
