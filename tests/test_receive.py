from .fixtures import client

from time import time_ns


def test_receive(caplog, client):
    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_receive"
    payload = str(time_ns()).encode("utf-8")

    subscription = client.subscribe(topic)
    assert subscription.wait_for_active(1), "Subscription did not activate"

    pub_message = client.publish(topic=topic, payload=payload)
    pub_message.wait_for_communication()

    subscription.wait_for_message(1)

    sub_message = subscription.messages[0]
    sub_message_count = subscription.total_message_count

    assert (
        pub_message == sub_message
    ), "Sent and received message does not contain the same values"
    assert (
        pub_message is not sub_message
    ), "Sent and received messages are the same object, did the message go through a broker and return?"
    assert sub_message_count == 1, "Expected exactly 1 message to be received"
