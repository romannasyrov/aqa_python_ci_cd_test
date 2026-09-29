import logging
import time
from http import HTTPMethod
from urllib.parse import urljoin

import requests

from utils.retry import retry
from utils.timing import timing

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, host: str, headers: dict | None = None):
        self.host = host
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    def __enter__(self):
        self._start = time.perf_counter()
        logger.info(f"[ApiClient] Открыт для {self.host}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.session.close()
        except Exception as e:
            logger.warning(f"[ApiClient] Ошибка при закрытии: {e}")
        return False

    @retry(retries=3, base_delay=1.0)
    @timing
    def _request(self, endpoint: str, method: HTTPMethod, **kwargs) -> requests.Response:
        url = urljoin(self.host, endpoint)
        logger.info(f"{method} {url} | keys: {list(kwargs.keys())}")

        response = self.session.request(
            url=url,
            method=method,
            **kwargs,
        )
        logger.info(f"{response.status_code} {url}")
        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request(
            endpoint=endpoint,
            method=HTTPMethod.GET,
            **kwargs
        )

    def post(self, endpoint: str, json: dict | None = None, **kwargs) -> requests.Response:
        if json is not None:
            kwargs["json"] = json
        return self._request(
            endpoint=endpoint,
            method=HTTPMethod.POST,
            **kwargs
        )
