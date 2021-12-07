import pytest

from mqttwrapper import mqtt_client, mqtt_config


@pytest.fixture
def client():
    config = mqtt_config.MqttConfig("127.0.0.1", 1883)
    client = mqtt_client.MqttClient(config)

    return client
