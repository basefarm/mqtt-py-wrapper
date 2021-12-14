from typing import Callable
import time
import logging


def wait(
    condition: Callable,
    timeout: int = None,
    log: logging.Logger = None,
    reason: str = "",
    resolution: float = 100,
):
    """wait Timeout function

    Simplifies waiting for conditions with a timeout

    Args:
        condition (Callable): Function that determins if we can stop waiting
        timeout (int, optional): How long to wait before timing out, None means no timeout. Defaults to None.
        log (logging.Logger, optional): Logger object to use for logging. Defaults to None.
        reason (str, optional): Reason to give in the log. Defaults to "".
        resolution (float, optional): timeout devided by resolution = sleep interval, will never sleep longer than 1 second. Defaults to 100

    Returns:
        bool: If contidtion is true return True, if timeout return False
    """
    timeout_time = None if timeout is None else time.time() + timeout
    timeout_sleep = 1 if timeout is None else min(1, timeout / resolution)

    def timed_out():
        return False if timeout is None else time.time() > timeout_time

    while not condition() and not timed_out():
        time.sleep(timeout_sleep)
        elapsed = time.time() - (timeout_time - timeout)
        if log and round(elapsed, 1) % 1 == 0:
            log.info(
                "[{0:.2f}/{1:.2f} seconds elapsed] {2}".format(elapsed, timeout, reason)
            )

    return condition()
