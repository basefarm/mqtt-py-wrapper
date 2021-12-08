from .fixtures import client

from time import time_ns


def test_publish(caplog, client):
    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_publish"
    payload = time_ns()

    pub_message = client.publish(topic=topic, payload=payload)
    pub_message.wait_for_communication()

    assert (
        pub_message.is_communicated() == True
    ), "Did not receive confirmation that the message was received by broker"
