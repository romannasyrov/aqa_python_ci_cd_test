import requests

from clients.api_client import ApiClient
from clients.services.models.request_model import CreatePostRequest


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
            request_model: CreatePostRequest,
    ) -> requests.Response:
        return self.api_client.post(
            endpoint=Routes.POSTS,
            json=request_model.model_dump(),
        )
