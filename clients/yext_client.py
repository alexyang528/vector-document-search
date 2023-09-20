import requests
from typing import List, Optional
from yext import YextClient


class SuperYextClient(YextClient):

    """
    This class extends the base YextClient class with additional functionality, such as access to the CaC API.
    """

    endpoints = {
        "entity_type": "https://api.yext.com/v2/accounts/me/config/resourcenames/km/entity-type",
        "search_experience": "https://api.yext.com/v2/accounts/me/config/resources/answers/answers-config/{id}",
        "search_experiences": "https://api.yext.com/v2/accounts/me/config/resourcenames/answers/answers-config",
        "list_entities": "https://api.yextapis.com/v2/accounts/me/entities",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.v = "20230601"
        self.default_params = {"api_key": self.api_key, "v": self.v}

    def get_entity_types(self) -> List[str]:
        response = requests.get(
            self.endpoints["entity_type"],
            params=self.default_params,
        )

        if not response.ok:
            raise Exception(f"Error: {response.status_code}")

        entity_types = response.json()["response"]
        return entity_types

    def get_search_experiences(self) -> List[str]:
        response = requests.get(
            self.endpoints["search_experiences"],
            params=self.default_params,
        )

        if not response.ok:
            raise Exception(f"Error: {response.status_code}")

        search_experiences = response.json()["response"]
        return search_experiences

    def get_search_experience(self, experience_key: str) -> dict:
        full_url = self.endpoints["search_experience"].format(id=experience_key)
        response = requests.get(
            full_url,
            params=self.default_params,
        )
        if not response.ok:
            raise Exception(f"Error: {response.status_code}")
        return response.json()["response"]

    def list_entities(self, entity_type: str):
        response = requests.get(
            self.endpoints["list_entities"],
            params={**self.default_params, "entityTypes": entity_type},
        )
        if not response.ok:
            raise Exception(f"Error: {response.status_code}")
        return response.json()["response"]["entities"]

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
