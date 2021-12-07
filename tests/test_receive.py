from .fixtures import client

from time import time_ns


def test_receive(caplog, client):
    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_receive"
    payload = time_ns()

    subscription = client.subscribe(topic)

    pub_message = client.publish(topic, payload)
    pub_message.wait_for_communication()

    received = subscription.wait_for_message(1)
    assert received

    sub_message = subscription.messages[0]
    sub_message_count = subscription.total_message_count

    assert pub_message == sub_message
    assert sub_message_count == 1
