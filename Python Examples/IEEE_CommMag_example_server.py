# coding=utf-8
# !/usr/bin/env python3

import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f"{parentdir}/NEATpy")
sys.path.insert(0, f"{parentdir}")

from endpoint import *
from preconnection import *
from transport_properties import *
from security_parameters import *
from enumerations import *



def simple_receive_handler(connection, message, context, is_end, error):
    data = message.data.decode()
    shim_print(f"Got message with length {len(message.data)}: {data}", level='msg')
    connection.send(data.encode("utf-8"), None)

def new_connection_received(connection: Connection):
    connection.receive(simple_receive_handler)

if __name__ == "__main__":
    local_specifier = LocalEndpoint()
    local_specifier.with_port(5000)
    tp = TransportProperties()

    preconnection = Preconnection(local_endpoint=local_specifier, transport_properties=tp)
    new_listener = preconnection.listen()
    new_listener.HANDLE_CONNECTION_RECEIVED = new_connection_received

    preconnection.start()

