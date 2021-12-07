import logging
import random
import string
from typing import Tuple
from dataclasses import dataclass, field

import paho.mqtt.client as PahoClient
from .mqtt_userdata import MqttUserdata


def map_to_paho_protocol(protocol: str) -> int:
    protocol_map = {
        "3.1.0": {"ids": ["3", "3.1.0", "MQTTv3"], "paho_value": PahoClient.MQTTv31},
        "3.1.1": {
            "ids": ["4", "3.1.1", "MQTTv311", "MQTTv4"],
            "paho_value": PahoClient.MQTTv311,
        },
        "5.0.0": {"ids": ["5", "5.0.0", "MQTTv5"], "paho_value": PahoClient.MQTTv5},
    }

    for protocol_info in protocol_map.values():
        if protocol in protocol_info["ids"]:
            return protocol_info["paho_value"]

    all_ids_string = [protocol_info["ids"] for protocol_info in protocol_map.values()]
    raise ValueError(
        f"Invalid MQTT protocol '{protocol}', valid values are: {str(all_ids_string)}"
    )


@dataclass
class MqttConfig:

    host: str
    port: int
    username: str = None
    password: str = None
    transport: str = "tcp"

    protocol: str = "3.1.1"
    _protocol: str = field(init=False, repr=False, default="3.1.1")

    client_id: str = None
    _client_id: str = field(init=False, repr=False)

    tls: bool = False
    clean_session: bool = True
    keepalive: int = 60
    bind_address: str = ""

    log: logging.Logger = logging.getLogger("Config.INITIALIZING")
    save_sent_messages: bool = False

    def __post_init__(self):
        if self.client_id == None:
            client_id = "".join(random.choices(string.ascii_letters, k=20))
            self.client_id = str(client_id)
            self.log.debug(f"current: {self.client_id=}")
            self.log.info(
                "client_id not set, random ID generated {}".format(self.client_id)
            )

        self.log.name = "Config.{}".format(self.client_id)

    @property
    def client_id(self) -> str:
        client_id = self._client_id
        self.log.debug(f"client_id.getter() {client_id=}")
        return client_id

    @client_id.setter
    def client_id(self, client_id: str):
        self.log.debug(f"client_id.setter() {client_id=}")

        if not isinstance(client_id, str):
            self.log.debug(
                f"client_id: Expected value type string got '{type(client_id)}', setting to None"
            )
            self._client_id = None
            return

        paho_protocol_version = map_to_paho_protocol(self.protocol)
        if paho_protocol_version < PahoClient.MQTTv5 and len(client_id) > 23:
            self.log.warn(
                f"Client ID over 23 characters might not be supported on this protocol version {self._protocol}"
            )

        self._client_id = client_id

    @property
    def protocol(self) -> str:
        self.log.debug(f"protocol.getter() {self._protocol=}")
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: str):
        self.log.debug(f"protocol.setter() {protocol=}")

        if type(protocol) is property:
            self.log.debug(
                f"protocol: Expected value type string got '{type(protocol)}', setting to Class default"
            )
            self._protocol = MqttConfig._protocol
            return
        if map_to_paho_protocol(protocol):
            self._protocol = protocol

    def phao_config_client(self) -> Tuple[list, dict]:
        return (
            [],
            {
                "client_id": self.client_id,
                "clean_session": self.clean_session,
                "protocol": map_to_paho_protocol(self.protocol),
                "transport": self.transport,
            },
        )

    def paho_config_connect(self) -> Tuple[list, dict]:
        return (
            [
                self.host,
            ],
            {
                "port": self.port,
                "keepalive": self.keepalive,
                "bind_address": self.bind_address,
            },
        )
