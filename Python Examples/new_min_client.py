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
        # connection.close()
    if Connection.clone_count == 0:
        connection.receive(test)

    def clone_test(connection, message_data, message_context):
        shim_print("CLONE read {} bytes: {}".format(len(message_data), message_data), level="msg")

    def clone_handler(con):
        con.send("Hello from cloned connection 😅".encode('UTF-8'))
        con.receive(clone_test)

    if Connection.clone_count == 0:
        connection.clone(clone_handler)
        connection.send("Hello from first connection 😏".encode('UTF-8'))


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

    profile = None
    if len(sys.argv) > 1:
        profile = profiles_dict[sys.argv[1]]

    tp = TransportProperties(profile)

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)

    preconnection.set_event_handler(ConnectionEvents.RECEIVED, handle_received)
    preconnection.set_event_handler(ConnectionEvents.READY, ready_handler)

    preconnection.initiate()
    print(f'Seconds elapsed: {time.time() - start}')
