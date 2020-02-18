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
        connection.send("Hello from first connection 😏".encode('UTF-8'), None)


if __name__ == "__main__":
    start = int(time.time())

    local_specifier = LocalEndpoint()
    local_specifier.with_port(5000)

    ep = RemoteEndpoint()
    ep.with_address("weevil.info")
    ep.with_port(80)

    tp = TransportProperties('tcp')

    preconnection = Preconnection(local_endpoint=local_specifier, remote_endpoint=ep, transport_properties=tp)

    preconnection.set_event_handler(ConnectionEvents.RECEIVED, handle_received)
    preconnection.set_event_handler(ConnectionEvents.READY, ready_handler)

    preconnection.rendezvous()
    print(f'Seconds elapsed: {time.time() - start}')
