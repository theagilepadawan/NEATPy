# coding=utf-8
# !/usr/bin/env python3

from preconnection import *
from endpoint import *
from transport_properties import *
from enumerations import *


def sent_event_handler(connection):
    connection.receive()


def handle_received(connection):
    connection.close()


def handle_closed(connection):
    pass


def ready_handler(connection):
    connection.send("You're NEAT 😍".encode('UTF-8'))


if __name__ == "__main__":
    ep = RemoteEndpoint()
    ep.with_address("127.0.0.1")
    ep.with_port(5000)

    tp = TransportProperties()
    tp.require(SelectionProperties.ZERO_RTT_MSG)
    tp.prohibit(SelectionProperties.RELIABILITY)
    tp.ignore(SelectionProperties.CONGESTION_CONTROL)
    tp.ignore(SelectionProperties.PRESERVE_ORDER)
    tp.ignore(SelectionProperties.RETRANSMIT_NOTIFY)
    # tp.prefer(SelectionProperties.ZERO_RTT_MSG)

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)

    preconnection.set_event_handler(ConnectionEvents.RECEIVED, handle_received)
    preconnection.set_event_handler(ConnectionEvents.CONNECTION_RECEIVED, ready_handler)
    preconnection.set_event_handler(ConnectionEvents.SENT, sent_event_handler)

    preconnection.initiate()
