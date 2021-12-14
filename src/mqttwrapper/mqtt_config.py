import logging
import random
import string
from typing import Tuple
from dataclasses import dataclass, field
import ssl

import paho.mqtt.client as PahoClient
from .mqtt_userdata import MqttUserdata

# Help out with cyclic import
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .mqtt_client import MqttClient


def map_to_paho_protocol(protocol: str) -> int:
    protocol_map = {
        "3.1.0": {
            "ids": [PahoClient.MQTTv31, "3", "3.1.0", "MQTTv3"],
            "paho_value": PahoClient.MQTTv31,
        },
        "3.1.1": {
            "ids": [PahoClient.MQTTv311, "4", "3.1.1", "MQTTv311", "MQTTv4"],
            "paho_value": PahoClient.MQTTv311,
        },
        "5.0.0": {
            "ids": [PahoClient.MQTTv5, "5", "5.0.0", "MQTTv5"],
            "paho_value": PahoClient.MQTTv5,
        },
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
    """Configuration for mqtt client

    host: str
    port: int
    username: str = None
    password: str = None

        transport
            set to “websockets” to send MQTT over WebSockets. Leave at the default of “tcp” to use raw TCP.
        protocol
            the version of the MQTT protocol to use for this client. Can be either MQTTv31, MQTTv311 or MQTTv5
        client_id
            the unique client id string used when connecting to the broker. If client_id is zero length or None, then one will be randomly generated. In this case the clean_session parameter must be True.
        clean_session
            a boolean that determines the client type. If True, the broker will remove all information about this client when it disconnects. If False, the client is a durable client and subscription information and queued messages will be retained when the client disconnects.
            Note that a client will never discard its own outgoing messages on disconnect. Calling connect() or reconnect() will cause the messages to be resent. Use reinitialise() to reset a client to its original state.

    keepalive: int = 60
    bind_address: str = ""

    tls_enable: bool = False
    tls_insecure: bool = False

    log: logging.Logger = logging.getLogger("Config.INITIALIZING")
    save_sent_messages: bool = False

    Returns:
        MqttConfig: configuration object ment to be used by MqttClient
    """

    host: str
    port: int

    username: str = None
    password: str = None
    transport: str = "tcp"

    protocol: str = "3.1.1"
    _protocol: str = field(init=False, repr=False, default="3.1.1")

    client_id: str = None
    _client_id: str = field(init=False, repr=False)

    tls_enable: bool = False
    tls_insecure: bool = False

    clean_session: bool = True
    keepalive: int = 60
    bind_address: str = ""

    tls_enable: bool = False
    tls_insecure: bool = False

    log: logging.Logger = logging.getLogger("Config.INITIALIZING")
    save_sent_messages: bool = False

    __paho_need_reinitialize: bool = True
    __paho_need_reinitialize_slots: str = "protocol transport client_id clean_session"

    __paho_need_reconnect: bool = True
    __paho_need_reconnect_slots: str = "host port keepalive bind_address"

    def __post_init__(self):
        if self.client_id == None:
            client_id = "".join(random.choices(string.ascii_letters, k=20))
            self.client_id = str(client_id)
            self.log.debug(f"current: {self.client_id=}")
            self.log.info(
                "client_id not set, random ID generated {}".format(self.client_id)
            )

        self.log.name = "Config.{}".format(self.client_id)

        if (
            map_to_paho_protocol(self.protocol) == PahoClient.MQTTv5
            and self.clean_session
        ):
            self.log.warning(
                f"MQTTv5 does not use clean_session config, changing to None"
            )
            self.clean_session = None

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

    # Wrapper around private member
    @property
    def _paho_need_reinitialize(self) -> bool:
        return self.__paho_need_reinitialize

    def _phao_initialize(self, client: "MqttClient") -> bool:
        if self._paho_need_reinitialize:
            self.log.debug("Initializing paho")

            paho_client = PahoClient.Client(
                protocol=map_to_paho_protocol(self.protocol),
                transport=self.transport,
                client_id=self.client_id,
                clean_session=self.clean_session,
            )

            self.__paho_need_reinitialize = False

        else:
            paho_client = client._paho_client

        paho_client.user_data_set(client.userdata)

        if self.tls_enable:
            self.log.info(f"Enabling TLS")
            if not self.tls_insecure:
                # tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
                paho_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
                # tls_set_context(context=None)

            elif self.tls_insecure:
                self.log.warning(f"Disabling TLS cert verification")
                paho_client.tls_set(cert_reqs=ssl.CERT_NONE)
                paho_client.tls_insecure_set(self.tls_insecure)

        if self.transport == "websockets":
            self.log.debug("Setting websockets")
            # paho_client.ws_set_options(path="/mqtt", headers=None)

        client._paho_client = paho_client

    # Wrapper around private member
    @property
    def _phao_need_reconnect(self) -> bool:
        return self.__paho_need_reconnect

    def _paho_config(self, client: "MqttClient") -> bool:
        self.log.debug("Configuring paho")

        if self._paho_need_reinitialize:
            self._phao_inititialize(client)

        paho_client = client._paho_client

        self.log.debug(f"Paho client: {paho_client}")

        if self._phao_need_reconnect:
            paho_client.connect(
                host=self.host,
                port=self.port,
                keepalive=self.keepalive,
                bind_address=self.bind_address,
            )
