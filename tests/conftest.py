import logging

import pytest

from clients.api_client import ApiClient
from clients.services.adapter import PostsAdapter
from clients.services.post_service.service import PostsService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


@pytest.fixture(scope="session")
def api_client():
    return ApiClient(
        host="https://jsonplaceholder.typicode.com"
    )


@pytest.fixture(scope="session")
def posts_adapter(api_client):
    return PostsAdapter(api_client=api_client)


@pytest.fixture(scope="session")
def posts_service(posts_adapter) -> PostsService:
    return PostsService(adapter=posts_adapter)
