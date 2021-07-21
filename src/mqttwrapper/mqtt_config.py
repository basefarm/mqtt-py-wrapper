import logging
import random
import string
from typing import Tuple

import paho.mqtt.client as PahoClient
from .mqtt_userdata import MqttUserdata

class MqttConfig():

    PROTOCOL_VERSIONS = {
        "3.1.0": PahoClient.MQTTv31,
        "3.1.1": PahoClient.MQTTv311,
        "5.0.0": PahoClient.MQTTv5,
    }

    def __init__(self, host:str, port:int, username:str=None, password:str=None, transport:str="tcp", protocol:str="3.1.1", client_id:str=None, tls:bool=False, clean_session:bool=True, log:logging.Logger=None):
        self._log = log if log else logging.Logger("MqttConfig")

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.transport = transport
        self.protocol = protocol
        self.client_id = client_id
        self.tls = tls
        self.clean_session = clean_session
    
    @property
    def client_id(self) -> str:
        return self.__client_id
    @client_id.setter
    def client_id(self, client_id:str):
        if client_id == None:
            client_id = ''.join(
                random.choices(
                    string.ascii_letters,
                    k=16
                ))
            self._log.warning("client_id not set, random ID generated {}".format(client_id))
        self.__client_id = str(client_id)

    @property
    def save_sent_messages(self) -> bool:
        return self.__save_sent_messages
    @save_sent_messages.setter
    def save_sent_messages(self, enabled:bool):
        if not isinstance(enabled, bool):
            self._log.warning("save_sent_messages converting {} to bool".format(type(enabled)))
        self.__save_sent_messages = bool(enabled)

    @property
    def tls(self) -> bool:
        return self.__tls
    @tls.setter
    def tls(self, enabled:bool):
        if not isinstance(enabled, bool):
            self._log.warning("tls converting {} to bool".format(type(enabled)))
        self.__tls = bool(enabled)
    
    @property
    def protocol(self) -> str:
        protocol_versions={value:key for key, value in self.PROTOCOL_VERSIONS.items()}
        if self.__protocol in protocol_versions:
            return protocol_versions[self.__protocol]
        else:
            raise Exception("Internal protocol {} unknown")
    
    @protocol.setter
    def protocol(self, protocol:str):
        if protocol in self.PROTOCOL_VERSIONS:
            self.__protocol = self.PROTOCOL_VERSIONS[protocol]
        else:
            raise Exception("Protocol {} unknown, valid protocols are: {}".format(self.PROTOCOL_VERSIONS.keys()))

    @property
    def config_client(self) -> Tuple[list,dict]:
        return ([],
        {
            "client_id": self.client_id,
            "clean_session":self.clean_session,
            "protocol": self.protocol,
            "transport": self.transport,
        })

    @property
    def config_connect(self) -> Tuple[list,dict]:
        return (
            [
                self.host,
            ],
            {
                "port": self.port,
                "keepalive": self.keepalive,
                "bind_address": self.bind_address,
            }
        )