import logging
from time import sleep, perf_counter

import paho.mqtt.client as PahoClient
from paho.mqtt import reasoncodes as PahoReasonCodes

from .mqtt_config import MqttConfig
from .mqtt_userdata import MqttUserdata
from .mqtt_message import MqttMessage
from .mqtt_subscription import MqttSubscription


class MqttClient:
    def __init__(self, config: MqttConfig, log: logging.Logger = None):

        self.connection_status = PahoClient.MQTT_ERR_NO_CONN

        # Set parameters passed in to class
        self.config = config
        self.log = (
            log if log else logging.getLogger("Client.{}".format(self.config.client_id))
        )

        # Create userdata for this client
        self.userdata = MqttUserdata(self, log=self.log.getChild("Userdata"))

        # Create and configure Paho Client
        phao_config = self.config.phao_config_client()
        self._paho_client = PahoClient.Client(*phao_config[0], **phao_config[1])
        self._paho_client.enable_logger(logger=self.log.getChild("PahoClient"))
        self._paho_client.user_data_set(self.userdata)

        # Add callbacks to Paho Client
        self._paho_client.on_connect = self._on_connect
        self._paho_client.on_disconnect = self._on_disconnect
        self._paho_client.on_subscribe = self._on_subscribe
        self._paho_client.on_unsubscribe = self._on_unsubscribe
        # self._paho_client.on_publish = self._on_publish
        self._paho_client.on_message = self._on_message

    def subscribe(self, topic: str, qos: int = 1) -> MqttSubscription:

        subscription = self.userdata.subscribe(topic, qos)

        return subscription

    def unsubscribe(self, topic: str):
        for subscription in self.userdata.subscriptions():
            if subscription.topic == topic:
                self._paho_client.unsubscribe(topic)
                return subscription

    def start(self, blocking=True, timeout=60):
        config = self.config.paho_config_connect()

        self.log.info(f"Connecting to {config[0]}")

        self._paho_client.connect(*config[0], **config[1])
        self._paho_client.loop_start()

        start_time = perf_counter()
        elapsed_time = 0
        while (
            blocking and not self._paho_client.is_connected() and elapsed_time < timeout
        ):
            sleep(0.25)
            elapsed_time = perf_counter() - start_time
            self.log.info(f"Waiting for connection, {elapsed_time}seconds elapsed.")

    def stop(self):
        pass

    def publish(
        self, topic: str, payload: bytes, qos: int = 1, retain: bool = False
    ) -> MqttMessage:

        paho_message_info = self._paho_client.publish(
            topic, payload=payload, qos=qos, retain=retain
        )

        message = MqttMessage(
            userdata=self.userdata,
            mid=paho_message_info.mid,
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
            paho_message_info=paho_message_info,
        )

        return message

    def get_paho(self) -> PahoClient.Client:
        return self._paho_client

    def is_connected(self):
        return self._paho_client.is_connected()

    def _on_connect(self, paho_client, userdata, flags, rc):
        self.log.info(f"Connection code: {rc}")

        self.connection_status = rc

        if self.connection_status != PahoClient.MQTT_ERR_SUCCESS:
            self.log.error(
                f"Connection ERROR [{self.connection_status}]: {PahoReasonCodes(self.connection_status)}"
            )
            return

        for subscription in userdata.subscriptions:
            result, mid = paho_client.subscribe(subscription.topic, subscription.qos)
            subscription.mid = mid
            subscription.result = result

    def _on_disconnect(self, paho_client, userdata, rc):
        self.log.info("Disconnected")
        # unsub?
        # clean session?

    def _on_subscribe(self, paho_client, userdata, mid, granted_qos):
        self.log.info("Subscribed")
        subscription = userdata.get_subscription(mid=mid)
        subscription.subscribe_callback(granted_qos)
        paho_client.message_callback_add(
            subscription.topic, subscription.message_callback
        )

    def _on_unsubscribe(self, paho_client, userdata, mid):
        self.log.info("Unsubscribed")
        subscription = userdata.subscription(mid)
        paho_client.message_callback_remove(subscription.topic)
        subscription.unsubscribed()
        userdata.remove_subscription(subscription)

    # ? Dont think this is needed as we use MqttMessageInfo object instead
    # def _on_publish(self, paho_client, userdata, mid):
    #     sent_message = userdata.get_sent_message(mid)
    #     sent_message.published()

    def _on_message(self, paho_client, userdata, message):
        self.log.error(
            "Uncaught message. topic '{}', qos '{}', retain '{}', payload '{}'".format(
                message.topic, message.qos, message.retain, str(message.payload)
            )
        )
