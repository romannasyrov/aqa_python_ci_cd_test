import functools
import logging
import random
import time

import requests

logger = logging.getLogger(__name__)

def retry(
        retries: int = 3,
        base_delay: float = 1.0,
        retry_on_statuses: tuple[int, ...] = (500, 502, 503, 504)
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(retries):
                try:
                    response = func(*args, **kwargs)

                    if response.status_code in retry_on_statuses:
                        last_exception = requests.HTTPError(
                            f"HTTP {response.status_code}"
                        )
                        logger.warning(
                            f"{func.__name__}: попытка {attempt+1}/{retries}"
                            f"вернула {response.status_code}"
                        )
                    else:
                        return response
                except (requests.Timeout, requests.ConnectionError) as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__}: попытка {attempt + 1}/{retries} "
                        f"упала с {type(e).__name__}"
                    )

                if attempt == retries - 1:
                    logger.error(
                        f"{func.__name__}: все {retries} попытки исчерпаны"
                    )
                    raise last_exception

                delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
                logger.info(f"{func.__name__}: повтор через {delay:.2f}с")
                time.sleep(delay)

        return wrapper
    return decorator