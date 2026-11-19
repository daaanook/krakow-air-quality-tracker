"""Day 6: download JSON from an API and try again when the network or the server has a short problem."""
import logging
import time

import requests

log = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}  # "too many requests" and server-side errors


def get_json(url, params, attempts=3, backoff=2, timeout=30, sleep=time.sleep):
    """GET request that returns JSON. Waits 2, 4, ... seconds between attempts.

    A 4xx error such as 400 means our request is wrong, so repeating it makes no sense: it stops at once.
    """
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code in RETRY_STATUS:
                raise requests.HTTPError(f"server answered {response.status_code}", response=response)
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError, requests.Timeout) as error:
            problem = error
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else None
            if status not in RETRY_STATUS:
                raise
            problem = error
        if attempt == attempts:
            log.error("Giving up after %d attempts: %s", attempts, problem)
            raise problem
        wait = backoff ** attempt
        log.warning("Attempt %d of %d failed (%s). Waiting %d s", attempt, attempts, problem, wait)
        sleep(wait)
