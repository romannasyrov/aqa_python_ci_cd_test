import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

pytest_plugins = [
    "fixtures.worker_fixtures",
    "fixtures.api_fixtures",
]
