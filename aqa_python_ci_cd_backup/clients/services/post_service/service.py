from aqa_python_ci_cd.clients.services.adapter import PostsAdapter
from aqa_python_ci_cd.clients.services.models.request_model import CreatePostRequest


class PostsService:
    def __init__(self, adapter: PostsAdapter):
        self.adapter = adapter

    def create_post(self, title: str, body: str, userId: int):
        response = self.adapter.create_post(
            CreatePostRequest(
                title=title,
                body=body,
                userId=userId
            )
        )

        return response
