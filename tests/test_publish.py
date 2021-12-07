from .fixtures import client

from time import time_ns


def test_publish(caplog, client):
    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_publish"
    payload = time_ns()

    message = client.publish(topic, payload)
    message.wait_for_communication()

    assert message.is_communicated() == True
