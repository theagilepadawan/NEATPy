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


if __name__ == "__main__":
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

    def ready_handler(connection: Connection):
        shim_print("Connection is ready")
        connection.send(b"Simple hello", None)
        connection.receive(lambda con, msg, context, end, error: shim_print(f"Got msg: {msg}", level='msg'))

    connection_state_handler = ConnectionStateHandler()
    connection_state_handler.HANDLE_STATE_READY = ready_handler
    new_connection: Connection = preconnection.initiate()
    new_connection.state_handler = connection_state_handler

    preconnection.start()
