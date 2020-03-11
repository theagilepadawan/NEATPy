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

outer_con = None

def receive_handler(con, msg, context, end, error):
    shim_print(f"Got msg {len(msg.data)}: {msg.data.decode()}", level='msg')
    con.send(b"HEYA", None)
    con.receive(lambda con, msg, context, end, error: shim_print(f"Got msg {len(msg.data)}: {msg.data.decode()}", level='msg'))

def clone_ready(connection: Connection):
    shim_print("Clone is ready")
    connection.send(b"Simple clone hello", None)
    connection.receive(lambda con, msg, context, end, error: shim_print(f"Got msg {len(msg.data)}: {msg.data.decode()}", level='msg'))

def ready_handler(connection: Connection):
    shim_print("Connection is ready")
    connection.send(b"Simple hello", None)
    connection.receive(receive_handler)
    clone = connection.clone(None)
    clone.HANDLE_STATE_READY = clone_ready



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
    tp.add(ConnectionProperties.USER_TIMEOUT_TCP, {TCPUserTimeout.USER_TIMEOUT_ENABLED: True})

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)
#    preconnection.add_framer(framer.TestFramer())
#    preconnection.add_framer(framer.SecondFramer())
    outer_con: Connection = preconnection.initiate()
    outer_con.HANDLE_STATE_READY = ready_handler

    preconnection.start()
