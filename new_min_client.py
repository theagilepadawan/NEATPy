# coding=utf-8
# !/usr/bin/env python3

from preconnection import *
from endpoint import *
from transport_properties import *
from enumerations import *
import sys


def sent_event_handler(connection):
    connection.receive()


def handle_received(connection):
    connection.close()


def handle_closed(connection):
    pass


def ready_handler(connection):
    connection.send("You're NEAT 😍".encode('UTF-8'))



if __name__ == "__main__":
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
    preconnection.set_event_handler(ConnectionEvents.SENT, sent_event_handler)

    preconnection.initiate()
