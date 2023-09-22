import requests
from typing import List, Optional
from yext import YextClient


class SuperYextClient(YextClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.v = "20230601"
        self.default_params = {"api_key": self.api_key, "v": self.v}


    def chat_message(
        self,
        query: str,
        search_results: dict,
        bot_id: str,
    ):
        base_url = f"https://liveapi-us2.yext.com/v2/accounts/me/chat/{bot_id}/message"
        request_body = {
            "messages": [
                {
                "source": "BOT",
                "text": "Hi! How can I help you?",
                },
                {
                "source": "USER",
                "text": query,
                },
            ],
            "notes": {
                "currentGoal": "ANSWER_QUESTION",
                "queryResult": search_results,
                "searchQuery": query,
                "currentStepIndices": [1],
            },
            "promptPackage": "stable",
            "version": "STAGING"
        }

        response = requests.post(base_url, json=request_body, params={**self.default_params})
        response.raise_for_status()

        return response.json()["response"]["message"]["text"]

    
    def search_answers_vertical(
        self,
        query: str,
        experience_key: str,
        vertical_key: str,
        locale: str = "en",
        version: str = "PRODUCTION",
        headers: Optional[dict] = ...,
    ):
        """
        This method had to be reimplemented because there is a bug in the Yext Python SDK.
        """
        # The SDK pointed to the wrong thing!
        endpoint = "https://liveapi-us2.yext.com/v2/accounts/me/search/vertical/query"
        params = {
            "input": query,
            "api_key": self.api_key,
            "locale": locale,
            "v": self.v,
            "experienceKey": experience_key,
            "version": version,
            "verticalKey": vertical_key,
        }
        response = requests.get(endpoint, params=params).json()
        return response
