# coding=utf-8
# !/usr/bin/env python3
import os, sys, inspect, time


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f"{parentdir}/NEATpy")

from preconnection import *
from endpoint import *
from transport_properties import *
from enumerations import *
from connection_properties import TCPUserTimeout
import framer


def sent_event_handler(connection):
    pass


def handle_received(connection):
    pass


def handle_closed(connection):
    pass


# Handler to be passed to receive
def test(connection, message, message_context, end, error):
    shim_print("Read {} bytes: {}".format(len(message), message), level="msg")


def ready_handler(connection):
    connection.send(b"GET / HTTP/1.1\r\nHost: vg.no\r\n\r\n\r\n", None)
    connection.receive(test, min_incomplete_length=50000)


if __name__ == "__main__":
    profiles_dict = {
        "udp": TransportPropertyProfiles.UNRELIABLE_DATAGRAM,
        "tcp": TransportPropertyProfiles.RELIABLE_INORDER_STREAM,
        "sctp": TransportPropertyProfiles.RELIABLE_MESSAGE
    }

    ep = RemoteEndpoint()
    ep.with_address("195.88.54.16")
    ep.with_port(443)

    profile = None
    if len(sys.argv) > 1:
        profile = profiles_dict[sys.argv[1]]

    tp = TransportProperties(profile)

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)

    con = preconnection.initiate()
    con.HANDLE_STATE_READY = ready_handler

    preconnection.start()
