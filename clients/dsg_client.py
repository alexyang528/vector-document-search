import requests
import os
import json
from typing import Optional, Literal, Dict, List, Union, Any

Message = Dict[str, str]
Function = Dict[str, Union[str, Any]]
FunctionCall = Dict[str, str]

from pydantic import BaseModel
from typing import List, Optional


class FunctionCall(BaseModel):
    name: str
    # This is a serialized JSON. If you want to deserialize it into another Pydantic model, you can!
    arguments: str


class Message(BaseModel):
    role: str
    content: Optional[str]
    function_call: Optional[FunctionCall]


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage


class DSGClient:
    api_key: str
    v: str
    endpoint: str

    def __init__(self, api_key: Optional[str] = None, v: Optional[str] = "20231012"):
        key = api_key if api_key is not None else os.getenv("DSG_API_KEY")
        if key is None:
            raise ValueError(
                "Please provide an API key or set the DSG_API_KEY environment variable."
            )
        self.api_key = key
        self.v = v
        endpoint_template = (
            "https://liveapi.yext.com/v2/accounts/me/dsg2/invokeModel?api_key={key}&v={v}"
        )
        self.endpoint = endpoint_template.format(key=key, v=v)
        return

    def chat_completion(
        self,
        model: Literal["gpt-3.5-turbo", "gpt-4"],
        messages: List[dict],
        functions: Optional[List[Function]] = None,
        function_call: Optional[FunctionCall] = None,
        max_tokens=512,
        temperature=0,
    ):
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
        if functions is not None:
            request_body["jsonRequest"]["functions"] = functions
        if function_call is not None:
            request_body["jsonRequest"]["function_call"] = function_call

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

        return OpenAIResponse(**open_ai_response), response.json()["response"]["requestId"]
