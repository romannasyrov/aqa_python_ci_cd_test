import requests
from pydantic import BaseModel

from clients.api_client import ApiClient


class Routes:
    POSTS = "/posts"

    @classmethod
    def post_by_id(cls, post_id: int) -> str:
        return f"{cls.POSTS}/{post_id}"


class PostsAdapter:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    def create_post(
            self,
            request_model: BaseModel | dict,
    ) -> requests.Response:
        payload = request_model.model_dump(by_alias=True) if isinstance(request_model, BaseModel) else request_model
        return self.api_client.post(
            endpoint=Routes.POSTS,
            json=payload,
        )
