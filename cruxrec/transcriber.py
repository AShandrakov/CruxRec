import os
import asyncio
import logging
import tempfile
from urllib.parse import urlparse
from contextlib import asynccontextmanager

from yt_dlp import YoutubeDL
from openai import OpenAI


class Transcriber:
    """
    Class for video transcription.
    Uses OpenAI Whisper for audio transcription and falls back to speech_recognition if needed.
    The only public method is transcribe_from_url which requires only a video URL.
    """

    def __init__(
        self,
        whisper_api_key: str,
        default_language: str = "en-US",
        cookies_path: str = "./cookies.txt",
    ):
        """
        :param whisper_api_key: API key for Whisper.
        :param whisper_api_base: Base URL for Whisper API (e.g., "https://api.openai.com/v1").
        :param default_language: Fallback language for speech_recognition.
        :param cookies_path: Path to cookies.txt if needed.
        """
        self.whisper_api_key = whisper_api_key
        self.default_language = default_language
        self.cookies_path = cookies_path
        self.logger = logging.getLogger("serivces")

    async def transcribe_from_url(self, url: str, max_duration_s: int = 300) -> str:
        """
        Public method to transcribe a video from its URL.
        1. Downloads the video.
        2. Extracts audio using ffmpeg.
        3. Transcribes audio via the Whisper API; falls back to speech_recognition on error.

        :param url: Video URL.
        :param max_duration_s: Maximum allowed duration (default is 5 minutes).
        :return: Transcribed text or empty string on error.
        """
        video_file = None
        transcription = ""
        try:
            video_file = await self._download_video(url, max_duration_s)
            self.logger.info(f"Downloaded video: {video_file}")
            async with self._extract_audio(video_file) as audio_file:
                self.logger.info(f"Extracting audio from: {audio_file}")
                transcription = await self._transcribe_audio(audio_file)
                self.logger.info(f"Transcription: {transcription}")
        except Exception as e:
            self.logger.exception("Error during transcription:", exc_info=e)
        finally:
            if video_file and os.path.exists(video_file):
                os.remove(video_file)
        return transcription

    async def _download_video(self, url: str, max_duration_s: int) -> str:
        """
        Private method to download a video using yt-dlp.
        Uses a template with the hostname and %(id)s to ensure uniqueness.
        """
        parsed_url = urlparse(url)
        ydl_opts = {
            "cookies": self.cookies_path,
            "outtmpl": f"{parsed_url.hostname}-%(id)s.%(ext)s",
            "noplaylist": True,
            "quiet": True,
        }
        self.logger.info("yt-dlp options: %r", ydl_opts)
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            if not info_dict:
                raise RuntimeError(
                    "extract_info returned None. Check the URL or yt-dlp settings."
                )
            video_duration = info_dict.get("duration", 0)
            if video_duration <= max_duration_s:
                ydl.download([url])
                return ydl.prepare_filename(info_dict)
            else:
                raise ValueError("Video is longer than allowed 5 minutes")

    @asynccontextmanager
    async def _extract_audio(self, video_file: str):
        """
        Private asynchronous context manager to extract audio using ffmpeg.
        Creates a temporary m4a audio file.
        """
        audio_file = video_file.rsplit(".", 1)[0] + ".m4a"
        command = ["ffmpeg", "-i", video_file, "-q:a", "0", "-map", "a", audio_file]
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg exited with code {process.returncode}\n{stderr.decode()}"
                )
            yield audio_file
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)
            if process and process.returncode is None:
                process.terminate()

    async def _transcribe_audio(self, audio_path: str) -> str:
        """
        Private method to transcribe audio.
        Checks the audio codec using ffprobe and converts to PCM WAV if needed.
        Tries transcription via the Whisper API and falls back to speech_recognition on error.
        """
        wav_audio_path = None
        codec_command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        codec_process = await asyncio.create_subprocess_exec(
            *codec_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        codec_stdout, codec_stderr = await codec_process.communicate()
        codec = codec_stdout.decode().strip()

        try:
            if codec != "pcm_s16le":
                wav_audio_path = tempfile.mktemp(suffix=".wav")
                conversion_command = [
                    "ffmpeg",
                    "-i",
                    audio_path,
                    "-acodec",
                    "pcm_s16le",
                    "-y",
                    wav_audio_path,
                ]
                proc = await asyncio.create_subprocess_exec(*conversion_command)
                await proc.communicate()
                audio_path = wav_audio_path
                self.logger.info(f"Audio converted to WAV: {wav_audio_path}")

            self.logger.info(f"Transcribing {audio_path} via Whisper API...")
            client = OpenAI(api_key=self.whisper_api_key)
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="Systran/faster-whisper-medium", file=audio_file
                )
                return transcript.text
        except Exception as e:
            self.logger.exception("Error using Whisper API:", exc_info=e)
            self.logger.error("Falling back to speech_recognition...")
            return ""
        finally:
            if wav_audio_path and os.path.exists(wav_audio_path):
                os.remove(wav_audio_path)
