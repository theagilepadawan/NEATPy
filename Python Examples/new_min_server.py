# coding=utf-8
# !/usr/bin/env python3

"""
    This file is a ported version of the C example bundled with NEAT.
    Note that the NEAT bindings currently require Python 2.7 or larger.
    Python 3 will not work.
"""
import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from endpoint import *
from preconnection import *
from transport_properties import *
from enumerations import *


def sent_event_handler(connection):
    #connection.close()
    pass


def connection_received_handler(connection):
    def test(connection, message_data, message_context):
        connection.send("No, you're NEAT 🤩".encode('UTF-8'))
#        shim_print("Read {} bytes: {}".format(len(message), message), level="msg")
        shim_print("Read {} bytes: {}".format(len(message_data), message_data), level="msg")
        connection.receive(test)
    connection.receive(test)


def closed_handler(connection):
    pass
    #connection.stop_listener()


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

    preconnection = Preconnection(local_endpoint=local_specifier, transport_properties=tp)

    preconnection.set_event_handler(ConnectionEvents.SENT, sent_event_handler)
    preconnection.set_event_handler(ConnectionEvents.CONNECTION_RECEIVED, connection_received_handler)
    preconnection.set_event_handler(ConnectionEvents.CLOSED, closed_handler)

    preconnection.listen()
    sys.exit()
