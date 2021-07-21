import logging
import paho.mqtt.client as PahoClient

from .mqtt_config import MqttConfig
from .mqtt_userdata import MqttUserdata
from .mqtt_message import MqttMessage
from .mqtt_subscription import MqttSubscription
from .mqtt_publish import MqttPublish


class MqttClient():

    def __init__(self, config:MqttConfig=None, log:logging.Logger=None):
        self._log = log if log else logging.Logger("Client.{}".format(self._config.client_id()))
        self.config = config

        config = self._config.config_client
        self._paho_client = PahoClient(*config[0], **config[1])
        self._paho_client.enable_logger(logger=self._log.getChild("PahoClient"))
        self.userdata = MqttUserdata(log=self._log.getChild("Userdata"))
        self._paho_client.user_data_set(self.userdata)

        self._paho_client.on_connect = self._on_connect
        self._paho_client.on_disconnect = self._on_disconnect
        self._paho_client.on_subscribe = self._on_subscribe
        self._paho_client.on_unsubscribe = self._on_unsubscribe
        self._paho_client.on_publish = self._on_publish

        self._paho_client.on_message = self._on_message

    def subscribe(self, topic:str, qos:int=0) -> MqttSubscription:
        subscription = MqttSubscription(
            topic = topic,
            log = self._log.getChild("Subscription.{}".format(self.config.client_id, topic)),
        )
        self.userdata.add_subscription(subscription)

        return subscription

    def unsubscribe(self, topic:str):
        for subscription in self.userdata.subscriptions():
            if subscription.topic == topic:
                self._paho_client.unsubscribe(topic)
                return subscription

    def start(self):
        config = self._config.config_connect
        self._paho_client.connect(*config[0], **config[1])

    def stop(self):
        pass

    def publish(self, topic:str, payload:bytes=None, qos:int=1, retain:bool=False):
        paho_message_info = self._paho_client.publish(topic, payload=payload, qos=qos, retain=retain)
        message = MqttMessage(mid=paho_message_info.mid, rc=paho_message_info.rc, topic=topic, payload=payload, qos=qos, retain=retain)
        self.userdata.add_sent_message(message)

    def _on_connect(self, paho_client, userdata, flags, rc):
        self._log.info("Connected")

        for subscription in userdata.subsriptions():
            result, mid = paho_client.subscribe(subscription.topic, subscription.qos)
            subscription.mid = mid
            subscription.result = result

    def _on_disconnect(self, paho_client, userdata, rc):
        self._log.info("Disconnected")
        # unsub?
        # clean session?

    def _on_subscribe(self, paho_client, userdata, mid, granted_qos):
        self._log.info("Subscribed")
        subscription = userdata.subscription(mid)
        subscription.subscribed(granted_qos)
        paho_client.message_callback_add(subscription.topic, subscription.message_callback)

    def _on_unsubscribe(self, paho_client, userdata, mid):
        self._log.info("Unsubscribed")
        subscription = userdata.subscription(mid)
        paho_client.message_callback_remove(subscription.topic)
        subscription.unsubscribed()
        userdata.remove_subscription(subscription)

    def _on_publish(self, paho_client, userdata, mid):
        sent_message = userdata.get_sent_message(mid)
        sent_message.published()

    def _on_message(self, paho_client, userdata, message):
        self._log.error(
            "Uncaught message. topic '{}', qos '{}', retain '{}', payload '{}'".format(
                message.topic,
                message.qos,
                message.retain,
                str(message.payload)
        ))

        received_message = MqttMessage(
            topic = message.topic,
            qos = message.qos,
            retain = message.retain,
            payload = message.payload,
            log = self._log.getChild("MqttMessage")
        )
        userdata.add_received_message(received_message)
