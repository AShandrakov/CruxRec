import requests
from abc import ABC, abstractmethod
from requests import RequestException


class Summarizer(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Returns a summary (digest) for the given text."""
        pass


class GeminiSummarizer(Summarizer):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def __init__(self, key: str, prompt: str, timeout: float = 10.0) -> None:
        self.key = key
        self.prompt = prompt
        self.timeout = timeout
        self.session = requests.Session()

    def summarize(self, text: str) -> str:
        url = f"{self.BASE_URL}?key={self.key}"
        full_prompt = f"{self.prompt}:\n\n{text}"
        data = {"contents": [{"parts": [{"text": full_prompt}]}]}
        headers = {"Content-Type": "application/json"}
        try:
            response = self.session.post(
                url, json=data, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
        except RequestException as e:
            raise RuntimeError(f"Error making request to Gemini API: {e}") from e

        try:
            resp_json = response.json()
        except ValueError as e:
            raise ValueError("Gemini response is not valid JSON") from e

        try:
            candidate = resp_json["candidates"][0]
            result_text = candidate["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Unexpected format of Gemini response: {response.text}"
            ) from e

        return result_text.strip()
