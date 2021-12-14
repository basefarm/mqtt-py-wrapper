from .fixtures import client
import time


def test_client_connection(caplog, client):
    caplog.set_level("DEBUG")

    exception = ""
    try:
        client.start(timeout=10)
    except ConnectionRefusedError as e:
        exception = e

    assert client.is_connected(), f"{exception=} Make sure you have a broker running."
