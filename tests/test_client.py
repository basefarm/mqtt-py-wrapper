import pytest
from mqttwrapper import mqtt_client

def get_client():
    client = mqtt_client.MqttClient