import os
import enum
import logging
import time
import typing
from typing import Optional

import pynng
from locust import User, task


class MQTTPacketType(enum.IntEnum):
    """
    Packet types taken from: https://github.com/emqx/NanoSDK/blob/2329154ed14d92e9ab3705de48c7b03a3373d776/include/nng/mqtt/mqtt_client.h
    """

    CONNECT = 0x01
    CONNACK = 0x02
    PUBLISH = 0x03
    PUBACK = 0x04
    PUBREC = 0x05
    PUBREL = 0x06
    PUBCOMP = 0x07
    SUBSCRIBE = 0x08
    SUBACK = 0x09
    UNSUBSCRIBE = 0x0A
    UNSUBACK = 0x0B
    PINGREQ = 0x0C
    PINGRESP = 0x0D
    DISCONNECT = 0x0E
    AUTH = 0x0F


class MQTTProtocolVersion(enum.IntEnum):
    """
    MQTT protocol version taken from: https://github.com/emqx/NanoSDK/blob/2329154ed14d92e9ab3705de48c7b03a3373d776/include/nng/mqtt/mqtt_client.h

    Available versions are: 5, 3.1.1 and 3.1
    """

    V5 = 5
    V3_1_1 = 4
    V3_1 = 3


class MessageContext(typing.NamedTuple):
    """Metadata associated with a message."""
    qos: int
    topic: str
    payload: str


class MQTTQUICClient(pynng.Mqtt_quic):
    """
    A wrapper arround the MQTT QUIC client provided by pynng.
    """

    def __init__(self, address: str) -> None:
        self.address = address
        self.protocol_version = MQTTProtocolVersion.V3_1_1
        super().__init__(address)

    def create_message(
        self,
        message_type: MQTTPacketType,
        context: typing.Optional[MessageContext] = None,
    ) -> pynng.Mqttmsg:
        msg = pynng.Mqttmsg()
        msg.set_packet_type(message_type)
        msg.set_connect_proto_version(self.protocol_version)

        if context is not None:
            logging.debug("building publish msg")
            msg.set_publish_topic(context.topic)
            msg.set_publish_qos(context.qos)
            msg.set_publish_payload(context.payload, len(context.payload))
        return msg

    def connect(self):
        connmsg = self.create_message(
            message_type=MQTTPacketType.CONNECT,
        )
        logging.debug(f"Connecting using QUIC to <{self.address}>")
        self.send_msg(connmsg)

    def publish(self, name):
        topic = "testtopic"
        ts = time.strftime("%s")
        qos = 0
        payload = f'{{"worker": "{name}", "ts": "{ts}", "qos": {qos} }}'
        msg_ctx = MessageContext(
            qos=qos,
            topic=topic,
            payload=payload,
        )
        pub_msg = self.create_message(
            message_type=MQTTPacketType.PUBLISH,
            context=msg_ctx,
        )
        self.send_msg(pub_msg)
        time.sleep(0.5)


class QUICUser(User):
    abstract = True
    client: Optional[MQTTQUICClient] = None

    def __init__(self, environment) -> None:
        host = os.environ.get("MQTT_BROKER_QUIC_HOST", "emqx")
        port = os.environ.get("MQTT_BROKER_QUIC_PORT", "14567")
        self.address = f"mqtt-quic://{host}:{port}"
        super().__init__(environment)


class QUICTest(QUICUser):
    def on_stop(self):
        if self.client is None:
            return
        self.client.close()
        self.environment.runner.quit()

    def on_start(self):
        self.client = MQTTQUICClient(self.address)
        self.client.connect()

    @task
    def publishing(self):
        if self.client is None:
            return
        if self.greenlet:
            name = self.greenlet.name
        else:
            name = ""
        self.client.publish(name)
