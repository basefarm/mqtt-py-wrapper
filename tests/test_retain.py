from .fixtures import client

from time import time_ns


def test_retain_create(caplog, client):

    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_retain_create"
    payload = time_ns()

    ###
    # Sub after pub

    pub_message = client.publish(topic=topic, payload=payload, retain=True)
    pub_message.wait_for_communication()

    subscription = client.subscribe(topic)
    subscription.wait_for_active(1)

    subscription.wait_for_message(1)

    sub_message = subscription.messages[-1]
    sub_message_count = subscription.total_message_count

    assert sub_message.retain, "Received messages does not have the retain flag set"
    assert (
        pub_message == sub_message
    ), "Sent and received message does not contain the same values"
    assert (
        pub_message is not sub_message
    ), "Sent and received messages are the same object, did the message go through a broker and return?"
    assert sub_message_count == 1, "Expected exactly 1 message to be received"

    ###
    # Sub after reconnect

    client.stop()
    client.start(timeout=3)

    subscription.wait_for_active(1)
    subscription.wait_for_message(1)

    sub_message_count = subscription.total_message_count

    assert (
        sub_message_count == 2
    ), "Expected exactly 2 message to be saved, did we not receive the retained message after reconnect?"


def test_retain_delete(caplog, client):

    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_retain_delete"
    payload = time_ns()

    ###
    # Sub before Pub

    pub_message = client.publish(topic=topic, payload=payload, retain=True)
    pub_message.wait_for_communication()

    subscription = client.subscribe(topic)
    subscription.wait_for_active(1)
    subscription.wait_for_message(1)

    sub_message = subscription.messages[-1]
    sub_message_count = subscription.total_message_count

    assert sub_message.retain, "Received messages does not have the retain flag set"
    assert (
        pub_message == sub_message
    ), "Sent and received message does not contain the same values"
    assert (
        pub_message is not sub_message
    ), "Sent and received messages are the same object, did the message go through a broker and return?"
    assert sub_message_count == 1, "Expected exactly 1 message to be received"

    ###
    # Delete and verify
    subscription.wait_for_active(1)

    pub_message = client.publish(topic=topic, payload=None, retain=True)
    pub_message.wait_for_communication()

    subscription.wait_for_message(1)

    sub_message = subscription.messages[-1]
    sub_message_count = subscription.total_message_count

    assert (
        sub_message_count == 2
    ), "Expected exactly 2 message to be saved, did we not receive the None/Empty retain message?"
    assert (
        pub_message is not sub_message
    ), "Sent and received messages are the same object, did the message go through a broker and return?"
    assert (
        len(sub_message.payload) == 0
    ), "Received message does not have a zero-length/empty payload"
