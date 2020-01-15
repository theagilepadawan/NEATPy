# coding=utf-8
# !/usr/bin/env python3
import neat_utils
from neat import *
import sys
import copy

import neat_utils
from utils import *
from enumerations import *


class Connection():
    connection_list = {}

    def __init__(self, ops, preconnection, connection_type):
        # NEAT specific
        self.__ops = ops
        self.__context = ops.ctx
        self.__flow = ops.flow
        self.transport_stack = neat_utils.get_transport_stack_used(ops.ctx, ops.flow)

        # Map connection for later callbacks fired
        fd = self.get_flow_fd(self.__flow)
        Connection.connection_list[fd] = self

        shim_print(f"Connection established - transport used: {self.transport_stack}")

        # Python specific
        self.connection_type = connection_type
        self.test_counter = 0
        self.msg_list = []
        self.received_called = False
        self.request_queue = []
        self.preconnection = preconnection
        self.props = copy.deepcopy(self.preconnection.transport_properties)

        self.event_handler_list = preconnection.event_handler_list

        self.__ops.on_readable = self.handle_readable
        self.__ops.on_writable = self.handle_writeable
        self.__ops.on_all_written = self.handle_all_written
        self.__ops.on_close = self.handle_closed

        neat_set_operations(self.__context, self.__flow, self.__ops)

        # Fire of Connection received handler (if present)
        if self.event_handler_list[ConnectionEvents.CONNECTION_RECEIVED] is not None:
            self.event_handler_list[ConnectionEvents.CONNECTION_RECEIVED](self)

        if self.event_handler_list[ConnectionEvents.READY] is not None:
            self.event_handler_list[ConnectionEvents.READY](self)
        return

    def send(self, message_data, end_of_message=True):
        shim_print("SEND CALLED")
        self.msg_list.append(message_data)

    def receive(self):
        self.received_called = True

    def close(self):
        neat_close(self.__ops.ctx, self.__ops.flow)

    @staticmethod
    def handle_writeable(ops):
        shim_print("ON WRITABLE CALLBACK")

        connection = Connection.get_connection_by_operations_struct(ops)
        message_to_be_sent = connection.msg_list.pop()
        try:
            neat_write(ops.ctx, ops.flow, message_to_be_sent, len(message_to_be_sent), None, 0)
        except:
            shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))

        ops.on_writable = None
        neat_set_operations(ops.ctx, ops.flow, connection.ops)

        return NEAT_OK

    @staticmethod
    def handle_all_written(ops):
        shim_print("ALL WRITTEN")
        connection = Connection.get_connection_by_operations_struct(ops)

        if connection.event_handler_list[ConnectionEvents.SENT] is not None:
            connection.event_handler_list[ConnectionEvents.SENT](connection)

        return NEAT_OK

    @staticmethod
    def handle_readable(ops):
        shim_print("HANDLE READABLE")
        connection = Connection.get_connection_by_operations_struct(ops)
        if connection.received_called:
            neat_utils.read(ops)
        if connection.event_handler_list[ConnectionEvents.RECEIVED] is not None:
            connection.event_handler_list[ConnectionEvents.RECEIVED](connection)
        return NEAT_OK

    @staticmethod
    def handle_closed(ops):
        shim_print("HANDLE CLOSED")
        connection = Connection.get_connection_by_operations_struct(ops)

        if connection.event_handler_list[ConnectionEvents.CLOSED] is not None:
            connection.event_handler_list[ConnectionEvents.CLOSED]()

        if connection.connection_type == 'active':
            neat_stop_event_loop(ops.ctx)
        return NEAT_OK

    @staticmethod
    def get_flow_fd(flow):
        return neat_get_socket_fd(flow)

    @staticmethod
    def get_connection_by_operations_struct(ops):
        fd = Connection.get_flow_fd(ops.flow)
        return Connection.connection_list[fd]

    class ConnectionState(Enum):
        CREATED = auto()
        ESTABLISHED = auto()
        CLOSED = auto()
