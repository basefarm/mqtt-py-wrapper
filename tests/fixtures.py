from typing import Iterator
import pytest
import itertools

from mqttwrapper import mqtt_client, mqtt_config

# Create all parameters combinations.
host = ["127.0.0.1"]

# These are interdependant
port_transport_tls = [
    "1883-tcp-False",
    "8883-tcp-True",
    "8083-websockets-False",
    "8084-websockets-True",
]
protocol = [
    "3.1.0",
    "3.1.1",
    "5.0.0",
    "3",
    "4",
    "5",
    "MQTTv3",
    "MQTTv4",
    "MQTTv311",
    "MQTTv5",
]


@pytest.fixture(params=itertools.product(host, port_transport_tls, protocol))
def client(request, caplog, pytestconfig):
    caplog.set_level("DEBUG")

    host = request.param[0]
    port = int(request.param[1].split("-")[0])
    username = pytestconfig.getoption('username')
    password = pytestconfig.getoption('password')
    transport = request.param[1].split("-")[1]
    tls = "True" == request.param[1].split("-")[2]
    protocol = request.param[2]

    config = mqtt_config.MqttConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        transport=transport,
        tls_enable=tls,
        tls_insecure=True,
        protocol=protocol,
    )

    client = mqtt_client.MqttClient(config)

    return client
