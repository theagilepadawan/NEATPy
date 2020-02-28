# coding=utf-8
# !/usr/bin/env python3

import os, sys, inspect


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from endpoint import *
from preconnection import *
from transport_properties import *
from enumerations import *
import framer

if __name__ == "__main__":
    local_specifier = LocalEndpoint()
    local_specifier.with_port(5000)

    profiles_dict = {
        "udp": TransportPropertyProfiles.UNRELIABLE_DATAGRAM,
        "tcp": TransportPropertyProfiles.RELIABLE_INORDER_STREAM,
        "sctp": TransportPropertyProfiles.RELIABLE_MESSAGE
    }

    profile = None
    if len(sys.argv) > 1:
        profile = profiles_dict[sys.argv[1]]

    tp = TransportProperties(profile)

    def simple_receive_handler(connection, message, context, is_end, error):
        shim_print(f"Got msg: {message.data.decode()}", level='msg')
        connection.send(b"Simple server hello", None)

    def new_connection_received(connection: Connection):
        connection.receive(simple_receive_handler)


    preconnection = Preconnection(local_endpoint=local_specifier, transport_properties=tp)
    preconnection.add_framer(framer.TestFramer())
    new_listener: Listener = preconnection.listen()

    listen_event_handler = ListenerStateHandler()
    listen_event_handler.HANDLE_CONNECTION_RECEIVED = new_connection_received
    new_listener.state_handler = listen_event_handler

    preconnection.start()
