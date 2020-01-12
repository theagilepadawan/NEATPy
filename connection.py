# coding=utf-8
# !/usr/bin/env python3

from neat import *
import sys
import copy
import pdb
from time import *
import ctypes
from utils import *
from callbacks import *


class Connection():
    con_list = {}

    def __init__(self, ops, preconnection, transport_stack):
        # NEAT specific
        self.__ops = ops
        self.__context = ops.ctx
        self.__flow = ops.flow
        self.msg_list = []
        self.msg_list.append(b"Testing message request queue")
        self.transport_stack = transport_stack

        # Map connection for later callbacks fired
        fd = self.get_flow_fd(self.flow)
        Connection.con_list[fd] = self

        shim_print(f"Connection established - transport used: {transport_stack}")

        # Python specific
        self.test_counter = 0
        self.received_called = False
        self.request_queue = []
        self.preconnection = preconnection
        self.props = copy.deepcopy(self.preconnection.transport_properties)

        self.receive_handler = preconnection.receive_handler
        self.sent_handler = lambda: shim_print(
            "My message got sent, and this is a callback handling it 😎")  # preconnection.sent_handler

        self.ops.on_readable = self.handle_readable
        self.ops.on_writable = self.handle_writeable
        self.ops.on_all_written = self.handle_all_written

        neat_set_operations(self.context, self.flow, self.ops)

        return

    def send(self, message_data):
        self.msg_list.append(message_data)

    @staticmethod
    def handle_writeable(ops):
        shim_print("ON WRITABLE CALLBACK")

        connection = Connection.get_connection_by_operations_struct(ops)
        message_to_be_sent = connection.msg_list.pop()

        neat_write(ops.ctx, ops.flow, message_to_be_sent, len(message_to_be_sent), None, 0)

        ops.on_writable = None
        neat_set_operations(ops.ctx, ops.flow, connection.ops)

        return NEAT_OK

    @staticmethod
    def handle_all_written(ops):
        connection = Connection.get_connection_by_operations_struct(ops)

        connection.sent_handler()

        neat_close(ops.ctx, ops.flow)
        return NEAT_OK

    @staticmethod
    def handle_readable(ops):
        read(ops)
        return NEAT_OK

    @staticmethod
    def get_flow_fd(flow):
        return neat_get_socket_fd(flow)

    @staticmethod
    def get_connection_by_operations_struct(ops):
        fd = Connection.get_flow_fd(ops.flow)
        return Connection.con_list[fd]
