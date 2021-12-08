from dataclasses import dataclass, field
import logging

from .mqtt_subscription import MqttSubscription

# Help out with cyclic import
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .mqtt_client import MqttClient
    from .mqtt_message import MqttMessage


@dataclass
class MqttUserdata:

    client: "MqttClient"
    subscriptions: List[MqttSubscription] = field(default_factory=list)
    sent_messages: List["MqttMessage"] = field(default_factory=list)
    log: logging.Logger = logging.getLogger("Userdata")

    def subscribe(self, topic: str, qos: int = 1):
        subscription = MqttSubscription(
            userdata=self, topic=topic, qos=qos, log=self.log.getChild(f"Subscription.{topic}")
        )
        self.subscriptions.append(subscription)

        return subscription

    def get_subscription(self, *, topic=None, mid=None) -> MqttSubscription:
        if topic and mid:
            for subscription in self.subscriptions:
                if subscription.mid == mid and subscription.topic == topic:
                    return subscription
        elif topic:
            for subscription in self.subscriptions:
                if subscription.topic == topic:
                    return subscription
        elif mid:
            for subscription in self.subscriptions:
                if subscription.mid == mid:
                    return subscription
        else:
            raise IndexError(f"Requested subscription not found: '{topic=}', '{mid=}'")

    def add_sent_message(self, message: "MqttMessage"):
        self.sent_messages.append(message)
