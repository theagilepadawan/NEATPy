# coding=utf-8
# !/usr/bin/env python3
import os, sys, inspect, time


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f"{parentdir}/NEATpy")

from preconnection import *
from endpoint import *
from transport_properties import *
from security_parameters import  *
from enumerations import *
from connection_properties import TCPUserTimeout


def receive_handler(con:Connection, msg, context, end, error):
    shim_print(f"Got message {len(msg.data)}: {msg.data.decode()}", level='msg')
    con.stop()


def ready_handler(connection: Connection):
    shim_print("Connection is ready")
    connection.send(b"Hello server", None)
    connection.receive(receive_handler)


if __name__ == "__main__":
    start = time.time()
    ep = RemoteEndpoint()
    ep.with_address("192.168.1.2")
    ep.with_port(5000)

    tp = TransportProperties(TransportPropertyProfiles.RELIABLE_INORDER_STREAM)

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)
    connection: Connection = preconnection.initiate()
    connection.HANDLE_STATE_READY = ready_handler

    preconnection.start()
    end = time.time()
    print(end - start)


