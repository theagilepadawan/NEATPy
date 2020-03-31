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


def receive_handler(con, msg, context, end, error):
    shim_print(f"Got message {len(msg.data)}: {msg.data.decode()}", level='msg')


def ready_handler(connection: Connection):
    shim_print("Connection is ready")
    connection.send(b"Secure hello", None)
    connection.receive(receive_handler)

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
    sp = SecurityParameters()

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp, security_parameters=sp)
    outer_con: Connection = preconnection.initiate()
    outer_con.HANDLE_STATE_READY = ready_handler

    preconnection.start()
