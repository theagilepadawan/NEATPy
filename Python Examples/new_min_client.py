# coding=utf-8
# !/usr/bin/env python3
import os, sys, inspect, time

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from preconnection import *
from endpoint import *
from transport_properties import *
from enumerations import *


def sent_event_handler(connection):
    pass


def handle_received(connection):
    pass


def handle_closed(connection):
    pass


def ready_handler(connection):  # Handler to be passed to receive

    def test(con, message_data, message_context):
        shim_print("Read {} bytes: {}".format(len(message_data), message_data), level="msg")
        con.receive(test)

    def clone_test(connection, message_data, message_context):
        shim_print("CLONE read {} bytes: {}".format(len(message_data), message_data), level="msg")

    def clone_handler(con):
        con.send("Hello from cloned connection 😅".encode('UTF-8'), None)
        con.receive(clone_test)

    def clone_handler_2(con):
        con.send("Hello from another cloned connection 😅".encode('UTF-8'), None)
        con.receive(clone_test)

    if Connection.clone_count == 0:
        connection.receive(test)
        # connection.clone(clone_handler)
        # connection.clone(clone_handler_2)
        msg_ctx = MessageContext()
        #msg_ctx.add(MessageProperties.RELIABLE_DATA_TRANSFER, True)
        #msg_ctx.add(MessageProperties.LIFETIME, 10)
        connection.send("Hello - I'm the first message to be sent".encode('UTF-8'), None, message_context=msg_ctx)
        msg_ctx = MessageContext()
        msg_ctx.add(MessageProperties.IDEMPOTENT, True)
        msg_ctx.add(MessageProperties.RELIABLE_DATA_TRANSFER, False)
        msg_ctx.add(MessageProperties.PRIORITY, 200)
        msg_ctx.add(MessageProperties.LIFETIME, 10)
        connection.send(("I'm the second message, but have a higher priority"*180).encode('UTF-8'), None, message_context=msg_ctx)
        msg_ctx = MessageContext()
        msg_ctx.add(MessageProperties.LIFETIME, 10)

        connection.send("Hello - I'm the third message, but with same priority as the first, so I should really be third".encode('UTF-8'), None, message_context=msg_ctx)


if __name__ == "__main__":
    start = int(time.time())
    profiles_dict = {
        "udp": TransportPropertyProfiles.UNRELIABLE_DATAGRAM,
        "tcp": TransportPropertyProfiles.RELIABLE_INORDER_STREAM,
        "sctp": TransportPropertyProfiles.RELIABLE_MESSAGE
    }

    ep = RemoteEndpoint()
    ep.with_address("127.0.0.1")
    ep.with_port(5000)
    ep.with_interface("lo0")

    profile = None
    if len(sys.argv) > 1:
        profile = profiles_dict[sys.argv[1]]

    tp = TransportProperties(profile)
    tp.add(GenericConnectionProperties.USER_TIMEOUT_TCP, {TCPUserTimeout.USER_TIMEOUT_ENABLED: True})

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)

    preconnection.set_event_handler(ConnectionEvents.RECEIVED, handle_received)
    preconnection.set_event_handler(ConnectionEvents.READY, ready_handler)

    preconnection.initiate()
    print(f'Seconds elapsed: {time.time() - start}')
