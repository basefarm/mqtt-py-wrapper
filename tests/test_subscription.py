from .fixtures import client
import mqttwrapper


def test_subscribe(caplog, client):
    caplog.set_level("DEBUG")

    client.start(timeout=1)

    topic = "test_subscribe"

    subscription = client.subscribe(topic=topic)

    assert isinstance(
        subscription, mqttwrapper.mqtt_subscription.MqttSubscription
    ), "subscribe returned the wrong class"
    assert (
        subscription.wait_for_active() == True
    ), "Did not receive SUBACK within the timeout period"
    assert subscription.is_active() == True, "SUBACK not received"
