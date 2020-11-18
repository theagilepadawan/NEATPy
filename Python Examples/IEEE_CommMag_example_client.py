# coding=utf-8
# !/usr/bin/env python3
import os, sys, inspect, time

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f"{parentdir}/NEATpy")
sys.path.insert(0, f"{parentdir}")

from preconnection import *
from endpoint import *
from transport_properties import *
from security_parameters import  *
from connection_properties import *
from enumerations import *
from connection_properties import TCPUserTimeout
from framer import *


class FiveBytesFramer(Framer):
    def start(self, connection): pass
    def stop(self, connection): pass

    def new_sent_message(self, connection, message_data, message_context, sent_handler, is_end_of_message):
        connection.message_framer.send(connection, 'HEADER'.encode("utf-8") + message_data,
                                       message_context, sent_handler, is_end_of_message)

    def handle_received_data(self, connection):
        header, context, is_end = connection.message_framer.parse(connection, 6, 6)
        connection.message_framer.advance_receive_cursor(connection, 6)
        connection.message_framer.deliver_and_advance_receive_cursor(connection, context, 5, True)


def clone_error_handler(con:Connection):
    print("Clone failed!")

def receive_handler(con:Connection, msg, context, end, error):
    print(f"Got message with length {len(msg.data)}: {msg.data.decode()}")

def ready_handler1(connection: Connection):
    connection.receive(receive_handler)    # enqueue reception
    connection.send(("FIVE!").encode("utf-8"), None)
    connection2 = connection.clone(clone_error_handler)
    connection2.HANDLE_STATE_READY = ready_handler2

def ready_handler2(connection: Connection):
    connection.receive(receive_handler)    # enqueue reception
    connection.send(("HelloWorld").encode("utf-8"), None)

if __name__ == "__main__":
    ep = RemoteEndpoint()
    ep.with_address("127.0.0.1")
    ep.with_port(5000)

    tp = TransportProperties()
    tp.require(SelectionProperties.RELIABILITY)
    tp.prohibit(SelectionProperties.PRESERVE_MSG_BOUNDARIES)   # Enforce TCP
 
    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)
    preconnection.add_framer(FiveBytesFramer())
    connection1 = preconnection.initiate()
    connection1.HANDLE_STATE_READY = ready_handler1

    preconnection.start()

