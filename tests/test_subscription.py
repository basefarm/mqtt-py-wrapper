from .fixtures import client


def test_subscribe(caplog, client):
    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_subscribe"

    subscription = client.subscribe(topic=topic)
    assert subscription.is_active() == True
