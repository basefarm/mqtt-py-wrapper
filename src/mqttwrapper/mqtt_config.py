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

    tls: dict = None

        clean_session
            a boolean that determines the client type. If True, the broker will remove all information about this client when it disconnects. If False, the client is a durable client and subscription information and queued messages will be retained when the client disconnects.
            Note that a client will never discard its own outgoing messages on disconnect. Calling connect() or reconnect() will cause the messages to be resent. Use reinitialise() to reset a client to its original state.

    keepalive: int = 60
    bind_address: str = ""
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

    tls: dict = None
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

@dataclass
class MqttTls:
    
    ca_certs
        a string path to the Certificate Authority certificate files that are to be treated as trusted by this client. If this is the only option given then the client will operate in a similar manner to a web browser. That is to say it will require the broker to have a certificate signed by the Certificate Authorities in ca_certs and will communicate using TLS v1.2, but will not attempt any form of authentication. This provides basic network encryption but may not be sufficient depending on how the broker is configured. By default, on Python 2.7.9+ or 3.4+, the default certification authority of the system is used. On older Python version this parameter is mandatory.
    certfile, keyfile
        strings pointing to the PEM encoded client certificate and private keys respectively. If these arguments are not None then they will be used as client information for TLS based authentication. Support for this feature is broker dependent. Note that if either of these files in encrypted and needs a password to decrypt it, Python will ask for the password at the command line. It is not currently possible to define a callback to provide the password.
    cert_reqs
        defines the certificate requirements that the client imposes on the broker. By default this is ssl.CERT_REQUIRED, which means that the broker must provide a certificate. See the ssl pydoc for more information on this parameter.
    tls_version
        specifies the version of the SSL/TLS protocol to be used. By default (if the python version supports it) the highest TLS version is detected. If unavailable, TLS v1.2 is used. Previous versions (all versions beginning with SSL) are possible but not recommended due to possible security problems.
    ciphers
        a string specifying which encryption ciphers are allowable for this connection, or None to use the defaults. See the ssl pydoc for more information.

    Must be called before connect*().
    tls_set_context()

    tls_set_context(context=None)

    Configure network encryption and authentication context. Enables SSL/TLS support.

    context
        an ssl.SSLContext object. By default, this is given by ssl.create_default_context(), if available (added in Python 3.4).

    If you’re unsure about using this method, then either use the default context, or use the tls_set method. See the ssl module documentation section about security considerations for more information.

    Must be called before connect*().
    tls_insecure_set()

    tls_insecure_set(value)
