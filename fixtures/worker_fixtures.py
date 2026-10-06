import os

import allure
import pytest

from utils.worker_utils import worker_scoped_id


@pytest.fixture(scope="session")
def worker_id() -> str:
    return os.getenv("PYTEST_XDIST_WORKER", "master")

@pytest.fixture(autouse=True)
def attach_worker_to_allure(worker_id):
    allure.dynamic.parameter("worker", worker_id)

@pytest.fixture(scope="session")
def worker_num(worker_id) -> int:
    if worker_id.startswith("gw"):
        return int(worker_id.replace("gw", ""))
    return 0


@pytest.fixture
def worker_post_data():
    return {
        "title": worker_scoped_id("post"),
        "body": worker_scoped_id("body"),
        "userId": 1,
    }