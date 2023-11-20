import requests

class GoogleClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://translation.googleapis.com/language/translate/v2"

    def translate_text(self, text, source_language="en", target_language="ja"):
        params = {
            "key": self.api_key,
            "q": text,
            "format": "text",
            "source": source_language,
            "target": target_language
        }

        response = requests.post(self.base_url, params=params)
        response.raise_for_status()

        translated_text = response.json()["data"]["translations"][0]["translatedText"]
        return translated_text
