import logging
import time
from http import HTTPMethod
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


class ApiClient():
    def __init__(self, host: str, headers: dict | None = None):
        self.host = host
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    def _request(self, endpoint: str, method: HTTPMethod, **kwargs) -> requests.Response:
        url = urljoin(self.host, endpoint)
        logger.info(f"{method} {url} | keys: {list(kwargs.keys())}")

        try:
            response = self.retry(
                lambda: self.session.request(
                    url=url,
                    method=method,
                    **kwargs,
                ),
                operation=f"{method} {url}",
            )
            logger.info(f"{response.status_code} {url}")
            return response
        except (requests.Timeout, requests.ConnectionError) as e:
            logger.error(f"{method} {url} | {type(e).__name__}: {e}")
            raise

    @staticmethod
    def retry(func, retries=3, base_delay=1, operation: str = "request"):
        for attempt in range(retries):
            try:
                return func()
            except (requests.Timeout, requests.ConnectionError):
                if attempt == retries - 1:
                    logger.error(f"Все {retries} попытки исчерпаны для '{operation}'")
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Попытка {attempt + 1}/{retries} упала, повтор через {delay}с.")
                time.sleep(delay)

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        response = self._request(
            endpoint=endpoint,
            method=HTTPMethod.GET,
            **kwargs
        )

        return response

    def post(self, endpoint: str, json: dict | None = None, **kwargs) -> requests.Response:
        if json is not None:
            kwargs["json"] = json

        response = self._request(
            endpoint=endpoint,
            method=HTTPMethod.POST,
            **kwargs
        )

        return response
