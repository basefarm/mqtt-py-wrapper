from dataclasses import dataclass, field
import logging
import time

# Paho lib
from paho.mqtt import client as PahoClient
from paho.mqtt.client import MQTTMessage as PahoMQTTMessage

# This lib
from .mqtt_message import MqttMessage

# Help out with cyclic import
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .mqtt_userdata import MqttUserdata


@dataclass
class MqttSubscription:

    userdata: "MqttUserdata"
    topic: str
    qos: int = 1
    log: logging.Logger = logging.getLogger("Subscription.INITIALIZING")

    messages: List["MqttMessage"] = field(default_factory=list)

    _total_message_count: int = field(init=False, default=0)
    _rc: int = field(init=False, default=PahoClient.MQTT_ERR_NO_CONN)
    _mid: int = field(init=False, default=None)
    _granted_qos: int = field(init=False, default=0)

    def __post_init__(self):
        if self.log.name == "Subscription.INITIALIZING":
            self.log.name = "Subscription.{}".format(self.topic)

        if self.userdata.client.is_connected():
            self.activate()

    @property
    def total_message_count(self) -> int:
        return self._total_message_count

    @property
    def rc(self) -> int:
        return self._rc

    @property
    def mid(self) -> int:
        return self._mid

    @property
    def granted_qos(self) -> int:
        return self._granted_qos

    def is_active(self) -> bool:
        if self._rc == PahoClient.MQTT_ERR_SUCCESS:
            return True

        return False

    def activate(self):
        paho_client = self.userdata.client.get_paho()

        self._rc, self._mid = paho_client.subscribe(self.topic, self.qos)

    def add_message(self, message: MqttMessage):
        self._total_message_count += 1
        self.messages.append(message)

    def wait_for_message(self, timeout: int = None):
        """wait_for_message Block until message arrive or timeout

        Args:
            timeout (int, optional): Max seconds to wait. Defaults to None, blocking forever

        Returns:
            bool: True if a message arrived before timeout
        """
        total_message_count = self._total_message_count

        timeout_time = None if timeout is None else time.time() + timeout
        timeout_sleep = None if timeout is None else min(1, timeout / 10.0)

        def timed_out():
            return False if timeout is None else time.time() > timeout_time

        while total_message_count == self._total_message_count and not timed_out():
            time.sleep(timeout_sleep)

        return True if total_message_count != self._total_message_count else False

    def subscribe_callback(self, granted_qos: int):
        self._granted_qos = granted_qos

    def message_callback(self, client, userdata, message: PahoMQTTMessage):
        MqttMessage(
            subscription=self,
            topic=message.topic,
            payload=message.payload,
            qos=message.qos,
            retain=message.retain,
            mid=message.mid,
        )
