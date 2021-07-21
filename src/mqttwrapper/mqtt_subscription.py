import logging

class MqttSubscription():
    def __init__(self, topic:str, qos:int=1, log:logging.Logger=None):
        self._log = log if not log == None else logging.Logger("MqttSubscription")
        
        self.topic = topic
        self.message_count = 0

    def message_callback(self, paho_client, userdata, message):
        self.message_count += 1
