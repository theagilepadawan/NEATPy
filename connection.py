# coding=utf-8
# !/usr/bin/env python3
from message_context import *
from neat import *
import sys
import copy

import backend
from utils import *
from typing import Callable, List, Tuple
from enumerations import *

Message_queue_object = Tuple[bytes, MessageContext]
Batch_struct = List[Message_queue_object]


class Connection:
    connection_list = {}
    receive_buffer_size = 32 * 1024 * 1024  # 32MB

    def __init__(self, ops, preconnection, connection_type, listener=None):
        # NEAT specific
        self.__ops = ops
        self.__context = ops.ctx
        self.__flow = ops.flow
        self.transport_stack = SupportedProtocolStacks(ops.transport_protocol)

        # Map connection for later callbacks fired
        fd = backend.get_flow_fd(self.__flow)
        Connection.connection_list[fd] = self

        shim_print(f"Connection established - transport used: {self.transport_stack.name}")

        # Python specific
        self.connection_type = connection_type
        self.test_counter = 0
        self.msg_list = []
        self.messages_passed_to_back_end = []
        self.receive_request_queue = []
        self.tcp_to_small_queue: List[bytes] = []

        self.close_called = False
        self.batch_in_session = False

        self.preconnection = preconnection
        self.listener = listener
        self.__props = copy.deepcopy(self.preconnection.transport_properties)

        self.event_handler_list = preconnection.event_handler_list

        # Fire off appropriate event handler (if present)
        if connection_type is "passive" and self.event_handler_list[ConnectionEvents.CONNECTION_RECEIVED]:
            self.event_handler_list[ConnectionEvents.CONNECTION_RECEIVED](self)
        if connection_type == 'active' and self.event_handler_list[ConnectionEvents.READY]:
            self.event_handler_list[ConnectionEvents.READY](self)
        ops.on_all_written = handle_all_written
        ops.on_close = handle_closed

        neat_set_operations(ops.ctx, ops.flow, ops)

    def send(self, message_data, message_context=MessageContext(), end_of_message=True):
        shim_print("SEND CALLED")

        # If the connection is closed, prohibit further sending
        if self.close_called:
            shim_print("Closed is called, no further sending is possible")
            return

        if self.batch_in_session:
            # Check if batch_struct is already present (i.e if this is the first send in batch or not)
            if isinstance(self.msg_list[-1], List):
                self.msg_list[-1].append(message_data, message_context)
            else:
                self.msg_list.append([message_data, message_context])
        else:
            self.msg_list.append((message_data, message_context))
        message_passed(self.__ops)

    def receive(self, handler, min_incomplete_length=None, max_length=None):
        shim_print("RECEIVED CALLED")
        if self.close_called:
            shim_print("Closed is called, no further reception is possible")
            return
        self.receive_request_queue.append((handler, min_incomplete_length, max_length))
        # If there is only one request in the queue, this means it was empty and we need to set callback
        if len(self.receive_request_queue) is 1:
            received_called(self.__ops)

    def batch(self, bacth_block: Callable[[], None]):
        self.batch_in_session = True
        bacth_block()
        self.batch_in_session = False

    def close(self):
        # Check if there is any messages left to pass to NEAT or messages that is not given to the network layer
        if self.msg_list or self.messages_passed_to_back_end:
            self.close_called = True
        else:
            neat_close(self.__ops.ctx, self.__ops.flow)

    def abort(self):
        backend.abort(self.__context, self.__flow)

    def get_transport_properties(self):
        return self.__props

    def clone(self):
        backend.clone(self.__context, self.__flow, self.preconnection.remote_endpoint.address, self.preconnection.remote_endpoint.port)
        return NotImplementedError

    def stop_listener(self):
        self.listener.stop()

    # Static methods
    @staticmethod
    def get_connection_by_operations_struct(ops):
        fd = backend.get_flow_fd(ops.flow)
        return Connection.connection_list[fd]


def handle_writable(ops):
    try:
        shim_print("ON WRITABLE CALLBACK")
        connection = Connection.get_connection_by_operations_struct(ops)

        # Socket is writable, write if any messages passed to the transport system
        if connection.msg_list:
            # Todo: Should we do coalescing of batch sends here?
            message_to_be_sent, context = connection.msg_list.pop(0)
            if backend.write(ops, message_to_be_sent):
                shim_print("Neat failed while writing")
                # Todo: Elegant error handling
            # Keep message until NEAT confirms sending with all_written
            connection.messages_passed_to_back_end.append((message_to_be_sent, context))
            if not connection.msg_list:
                # neat_utils.set_neat_callbacks(ops, (NeatCallbacks.ON_WRITABLE, None))
                ops.on_writable = None
                neat_set_operations(ops.ctx, ops.flow, ops)
    except:
        pass
    return NEAT_OK


def message_passed(ops):
    try:
        ops.on_writable = handle_writable
        neat_set_operations(ops.ctx, ops.flow, ops)
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))
    return NEAT_OK


def received_called(ops):
    try:
        ops.on_readable = handle_readable
        neat_set_operations(ops.ctx, ops.flow, ops)
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))
    return NEAT_OK


def handle_all_written(ops):
    try:
        shim_print("ALL WRITTEN")
        close = False
        connection = Connection.get_connection_by_operations_struct(ops)
        message, message_context = connection.messages_passed_to_back_end.pop(0)

        if connection.close_called and len(connection.messages_passed_to_back_end) == 0:
            shim_print("All messages passed down to the network layer - calling close")
            close = True
        elif message_context.props[MessageProperties.FINAL] is True:
            shim_print("Message is marked final, closing connection")
            close = True
        if close:
            neat_close(connection.__ops.ctx, connection.__ops.flow)

        if connection.event_handler_list[ConnectionEvents.SENT] is not None:
            connection.event_handler_list[ConnectionEvents.SENT](connection)
    except:
        shim_print("An error occurred: {}".format(sys.exc_info()[0]))

    return NEAT_OK


def handle_readable(ops):
    try:
        shim_print("HANDLE READABLE")
        connection: Connection = Connection.get_connection_by_operations_struct(ops)

        if connection.receive_request_queue:
            handler, min_length, max_length = connection.receive_request_queue.pop(0)
            msg = backend.read(ops, connection.receive_buffer_size)

            # UDP delivers complete messages, ignore length specifiers
            if connection.transport_stack is SupportedProtocolStacks.UDP or (min_length is None and max_length is None): # TODO: SCTP here?
                handler(connection, msg)
            elif connection.transport_stack is SupportedProtocolStacks.TCP or connection.transport_stack is SupportedProtocolStacks.MPTCP:
                if connection.tcp_to_small_queue:
                    msg = connection.tcp_to_small_queue.pop() + msg
                if min_length and min_length > len(msg):
                    connection.tcp_to_small_queue.append(msg)
                    connection.receive(handler, min_length, max_length)
                elif max_length and max_length < len(msg):
                    # TODO: Received partial handler should be called, how should it be registered?
                    raise NotImplementedError
                else:
                    handler(connection, msg)  # TODO: MessageContext
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))

    return NEAT_OK


def handle_closed(ops):
    try:
        shim_print("HANDLE CLOSED")
        connection = Connection.get_connection_by_operations_struct(ops)
        if connection.event_handler_list[ConnectionEvents.CLOSED] is not None:
            shim_print("CLOSED HANDLER")
            connection.event_handler_list[ConnectionEvents.CLOSED](connection)

        # If a Connection becomes finished before a requested Receive action can be satisfied,
        # the implementation should deliver any partial Message content outstanding..."
        if connection.receive_request_queue:
            if connection.tcp_to_small_queue:
                handler = connection.receive_request_queue.pop(0)[0] # Should check if there is more than one request in the queue
                shim_print("Sending leftovers")
                handler(connection, connection.tcp_to_small_queue.pop())
            # "...or if none is available, an indication that there will be no more received Messages."
            else:
                shim_print("Connection closed, there will be no more received messages")    # TODO: Should this be thrown as an error (error event?)
        if connection.connection_type == 'active': # should check if there is any cloned connections etc...
            backend.stop(ops.ctx)
    except:
        pass
    return NEAT_OK


class ConnectionState(Enum):
    CREATED = auto()
    ESTABLISHED = auto()
    CLOSED = auto()
