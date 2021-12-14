import logging
import time

import paho.mqtt.client as PahoClient

from .mqtt_config import MqttConfig, map_to_paho_protocol
from .mqtt_userdata import MqttUserdata
from .mqtt_message import MqttMessage
from .mqtt_subscription import MqttSubscription
from .helper import wait


class MqttClient:
    def __init__(self, config: MqttConfig, log: logging.Logger = None):

        self._paho_rc = PahoClient.MQTT_ERR_NO_CONN

        # Set parameters passed in to class
        self.config = config

        self.log = (
            log if log else logging.getLogger("Client.{}".format(self.config.client_id))
        )

        # Create userdata for this client
        self.userdata = MqttUserdata(self, log=self.log.getChild("Userdata"))

        # Create and configure Paho Client
        self.config._phao_initialize(self)

        self._paho_client.enable_logger(logger=self.log.getChild("PahoClient"))

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

    def start(self, blocking=True, timeout=None):

        self.log.info(f"Connecting to {self.config.host}:{self.config.port}")

        self.config._paho_config(self)

        self._paho_client.loop_start()

        if blocking:
            wait(
                condition=self.is_connected,
                timeout=timeout,
                log=self.log,
                reason="Waiting for conenction",
            )

        # timeout_time = None if timeout is None else time.time() + timeout
        # timeout_sleep = None if timeout is None else min(1, timeout / 100.0)

        # def timed_out():
        #     return False if timeout is None else time.time() > timeout_time

        # while blocking and not self.is_connected() and not timed_out():
        #     time.sleep(timeout_sleep)
        #     self.log.info(
        #         "Waiting for connection, {0:.2f}/{1:.2f} seconds elapsed.".format(
        #             time.time() - (timeout_time - timeout), timeout
        #         )
        #     )

    def stop(self):
        self.log.info(f"Disonnecting from {self.config.host}:{self.config.port}")
        self._paho_client.disconnect()
        self._paho_client.loop_stop()

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

    def _on_connect(self, paho_client, userdata, flags, rc, properties=None):
        self.log.info(f"Connection code: {rc}")

        self._paho_rc = rc

        if self._paho_rc != PahoClient.MQTT_ERR_SUCCESS:
            self.log.error(
                f"Connection ERROR [{self._paho_rc}]: {PahoClient.connack_string(self._paho_rc)}"
            )
            return

        for subscription in userdata.subscriptions:
            subscription.wait_for_active()

    def _on_disconnect(self, paho_client, userdata, rc, properties=None):

        self.log.info(f"Disconnected code: {rc}")

        self._paho_rc = rc

        for subscription in userdata.subscriptions:
            subscription.deactivate(self._paho_rc)

        if self._paho_rc != PahoClient.MQTT_ERR_SUCCESS:
            self.log.error(
                f"Disconnection ERROR (Unexpected) [{self._paho_rc}]: {PahoClient.connack_string(self._paho_rc)}"
            )

        return

    def _on_subscribe(self, paho_client, userdata, mid, granted_qos, properties=None):
        self.log.info(f"Subscribed: {mid=}")

        # Avoid race condition where callback triggers before subscribe call gets an RC.
        #   This is fairly rare, seem to be around every 1/1000 time or so on local computer network
        wait(
            condition=lambda: userdata.get_subscription(mid=mid) is not None,
            timeout=3,
            log=self.log,
            reason="Waiting for subscription",
            resolution=100,
        )

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
