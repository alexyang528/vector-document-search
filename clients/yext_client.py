import requests
from typing import Optional


class CustomYextClient():

    def __init__(self, api_key, environment=None):
        self.v = "20230601"
        self.api_key = api_key
        self.default_params = {"api_key": self.api_key, "v": self.v}
        self.environment = environment


    def chat_message(
        self,
        query: str,
        search_results: dict,
        bot_id: str,
        goal_id: str = "ANSWER_QUESTION",
        step_indices: list = [1],
    ):
        # domain = "liveapi-sandbox" if self.environment == "SANDBOX" else "liveapi-us2"
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
                "currentGoal": goal_id,
                "queryResult": search_results,
                "searchQuery": query,
                "currentStepIndices": step_indices,
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
        version: str = "STAGING",
        endpoint: str = None
    ):
        
        # domain = "liveapi-sandbox" if self.environment == "SANDBOX" else "liveapi-us2"
        base_url = f"https://liveapi-us2.yext.com/v2/accounts/me/search/vertical/query"

        # Override endpoint if provided
        base_url = endpoint if endpoint else base_url

        params = {
            "input": query,
            "api_key": self.api_key,
            "locale": locale,
            "v": self.v,
            "experienceKey": experience_key,
            "version": version,
            "verticalKey": vertical_key,
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
