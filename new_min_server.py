# coding=utf-8
# !/usr/bin/env python3

"""
    This file is a ported version of the C example bundled with NEAT.
    Note that the NEAT bindings currently require Python 2.7 or larger.
    Python 3 will not work.
"""

import sys
from time import *
from endpoint import *
from preconnection import *
from transport_properties import *
from enumerations import *


def sent_event_handler(connection):
    connection.close()


def received_handler(connection):
    connection.send("No, you're NEAT 😘".encode('UTF-8'))


def connection_received_handler(connection):
    connection.receive()


def closed_handler(connection):
    connection.stop_listener()


if __name__ == "__main__":
    local_specifier = LocalEndpoint()
    local_specifier.with_port(5000)

    tp = TransportProperties()
    preconnection = Preconnection(local_endpoint=local_specifier, transport_properties=None)

    preconnection.set_event_handler(ConnectionEvents.RECEIVED, received_handler)
    preconnection.set_event_handler(ConnectionEvents.SENT, sent_event_handler)
    preconnection.set_event_handler(ConnectionEvents.CONNECTION_RECEIVED, connection_received_handler)
    preconnection.set_event_handler(ConnectionEvents.CLOSED, closed_handler)

    preconnection.listen()
    sys.exit()
