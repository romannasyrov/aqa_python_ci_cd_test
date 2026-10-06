import os
import pytest

from utils.worker_utils import worker_scoped_id


@pytest.fixture(scope="session")
def worker_id() -> str:
    """ID воркера xdist: 'gw0', 'gw1', ... или 'master'."""
    return os.getenv("PYTEST_XDIST_WORKER", "master")


@pytest.fixture(scope="session")
def worker_num(worker_id) -> int:
    """Номер воркера: 0, 1, 2, ..."""
    if worker_id.startswith("gw"):
        return int(worker_id.replace("gw", ""))
    return 0


@pytest.fixture
def worker_post_data():
    """Генерирует worker-scoped данные для поста."""
    return {
        "title": worker_scoped_id("post"),
        "body": worker_scoped_id("body"),
        "userId": 1,
    }