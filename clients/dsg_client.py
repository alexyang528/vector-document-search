import requests
import os
import json

class DSGClient:
    api_key: str
    v: str
    endpoint: str

    def __init__(self, api_key, v="20231012"):
        
        endpoint_template = "https://liveapi.yext.com/v2/accounts/me/dsg2/invokeModel?api_key={key}&v={v}"
        self.endpoint = endpoint_template.format(key=api_key, v=v)
        return

    def chat_completion(self, model, messages, max_tokens=512, temperature=0):
        """
        Send a request to the DSG API to generate a chat response.
        This is a wrapper around the DSG API that handles the JSON formatting for you.
        """
        request_body = {
            "locale": "en",  # Always en
            "modelId": "openAiCompletions",
            "endpointId": "chatCompletions",
            "version": {"applicationVersion": "5"},
            "latencySensitive": False,
            "jsonRequest": {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            "skipCache": False,
        }

        response = requests.post(self.endpoint, json=request_body)

        if response.status_code != 200:
            with open("body.json", "w") as f:
                json.dump(request_body, f)
            print("--")
            raise ValueError(
                f"Request failed with status code {response.status_code}: {response.text}"
            )

        response.raise_for_status()
        open_ai_response = response.json()["response"]["jsonResponse"]

        return open_ai_response["choices"][0]["message"]["content"]
