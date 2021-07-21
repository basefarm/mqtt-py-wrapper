import logging

from .mqtt_message import MqttMessage
from .mqtt_subscription import MqttSubscription
from .mqtt_publish import MqttPublish

class MqttUserdata():
    def __init__(self, log:logging.Logger=None):
        self._log = log if not log == None else logging.Logger("MqttUserdata")
        