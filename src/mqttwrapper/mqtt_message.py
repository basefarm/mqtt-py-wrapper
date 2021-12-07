from dataclasses import dataclass, field
from time import time_ns

from paho.mqtt.client import MQTTMessageInfo as PahoMQTTMessageInfo

# Help out with cyclic import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mqtt_userdata import MqttUserdata
    from .mqtt_subscription import MqttSubscription


@dataclass()
class MqttMessage:
    topic: str
    payload: bytes
    qos: int
    retain: bool
    mid: int = field(repr=False, compare=False)

    userdata: "MqttUserdata" = field(repr=False, default=None, compare=False)
    subscription: "MqttSubscription" = field(repr=False, default=None, compare=False)

    paho_message_info: PahoMQTTMessageInfo = field(
        repr=False, default=None, compare=False
    )
    _timestamp_ns: int = field(
        init=False, repr=False, default_factory=time_ns, compare=False
    )

    def __post_init__(self):
        if self.userdata and not self.subscription:
            self.userdata.add_sent_message(self)
        elif self.subscription and not self.userdata:
            self.subscription.add_message(self)

        payload = self.payload
        if not isinstance(payload, bytes):
            if not isinstance(payload, str):
                payload = str(payload)
            payload = payload.encode("utf-8")

        self.payload = payload

    @property
    def timestamp_ns(self):
        return self._timestamp_ns

    def is_communicated(self) -> bool:
        """is_communicated Checks if message is published if self.paho_message_info is populated otherwise returnes True

        When self.paho_message_info is precent it is assumed this is an outgoing message and checks if it has been published using the function paho libs MQTTMessageInfo.is_published()

        If self.paho_message_info is None it is assumed this was a received message, which means it was communicated to us and this will always return True in that case

        Returns:
            bool: Has the message completed transmission
        """

        if self.paho_message_info:
            return self.paho_message_info.is_published()

        return True

    def wait_for_communication(self, timeout: int = 1) -> bool:
        """wait_for_communication waits for communication to complete up to timeout seconds

        This only have any real effect when this is an outgoing message, determined by the precense of self.paho_message_info

        Args:
            timeout (int, optional): [Max wait time in seconds]. Defaults to 1.

        Returns:
            bool: result is taken from self.is_communicated()
        """

        if self.paho_message_info:
            self.paho_message_info.wait_for_publish(timeout=timeout)

        return self.is_communicated()
