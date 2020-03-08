# coding=utf-8
# !/usr/bin/env python3
import inspect
import json
import math
import queue
import time
import sys
import copy
from dataclasses import dataclass, field
from enum import Enum, auto
from connection_properties import TCPUserTimeout, ConnectionProperties
from endpoint import LocalEndpoint, RemoteEndpoint
import message_framer
from enumerations import SupportedProtocolStacks, AdditionalServices, ServiceLevel, PreferenceLevel
from message_context import MessageContext
from message_properties import MessageProperties
from neat import *
import preconnection
from selection_properties import CommunicationDirections, SelectionProperties
import backend
from typing import Callable, List, Tuple, Any, Optional
from transport_properties import TransportProperties
from utils import shim_print
#from typeAliases import ReceiveHandlerTypeSignature, SentHandlerTypeSignature


class Connection:
    """ A Connection represents a transport Protocol Stack on which data can be sent to and/or received from a remote
    Endpoint (i.e., depending on the kind of transport, connections can be bi-directional or unidirectional).

    A Connection is created from a :py:class:`preconnection` or cloning, i.e it cannot be instantiated directly.
    """
    connection_list = {}
    receive_buffer_size = 32 * 1024 * 1024  # 32MB
    clone_count = 0
    static_counter = 0

    def __init__(self, preconnection, connection_type, listener=None, parent=None):

        # NEAT specific
        self.ops = None
        self.context = None
        self.flow = None
        self.transport_stack = None

        # Map connection for later callbacks fired
        Connection.static_counter += 1
        self.connection_id = Connection.static_counter
        Connection.connection_list[self.connection_id] = self

        # Python specific
        self.connection_type = connection_type
        self.clone_counter = 0
        self.test_counter = 0
        self.msg_list: queue.PriorityQueue = queue.PriorityQueue()
        self.messages_passed_to_back_end = []
        self.receive_request_queue = []
        self.buffered_message_data_object: MessageDataObject = None
        self.partitioned_message_data_object: MessageDataObject = None
        self.message_sent_with_initiate = None
        self.clone_callbacks = {}
        self.connection_group = []
        self.local_endpoint = None
        self.remote_endpoint = None
        self.framer_placeholder: FramerPlaceholder = FramerPlaceholder(connection=self)
        self.stack_supports_message_boundary_preservation = False

        # if this connection is a result from a clone, add parent
        if parent:
            shim_print(f"Connection is a result of cloning - Parent {parent}")
            self.connection_group.append(parent)

        self.close_called = False
        self.batch_in_session = False
        self.final_message_received = False
        self.final_message_passed = False

        self.HANDLE_STATE_READY: Callable[[], None] = None  #: Handler for when the connection transitions to ready state
        self.HANDLE_STATE_CLOSED: Callable[[], None] = None #: Handler for when the connection transitions to clsoed state
        self.HANDLE_STATE_CONNECTION_ERROR: Callable[[], None] = None #: Handler for when the connection gets experiences a connection error

        self.preconnection = preconnection
        self.transport_properties = self.preconnection.transport_properties
        self.listener = listener
        self.message_framer: message_framer.MessageFramer = preconnection.message_framer
        self.state = ConnectionState.ESTABLISHING

    def established_routine(self, ops):
        self.ops = ops
        self.context = ops.ctx
        self.flow = ops.flow
        self.transport_stack = SupportedProtocolStacks(ops.transport_protocol)
        self.transport_properties = copy.deepcopy(self.preconnection.transport_properties)

        if SupportedProtocolStacks.get_service_level(self.transport_stack, SelectionProperties.PRESERVE_MSG_BOUNDARIES) == ServiceLevel.INTRINSIC_SERVICE:
            self.stack_supports_message_boundary_preservation = True


        self.ops.connection_id = self.connection_id
        shim_print(f"Connection [ID: {self.connection_id}] established - transport used: {self.transport_stack.name}", level='msg')
        #self.set_connection_properties()

        # Fire off appropriate event handler (if present)
        if self.HANDLE_STATE_READY:
            self.HANDLE_STATE_READY(self)

        ops.on_all_written = handle_all_written
        ops.on_close = handle_closed

        neat_set_operations(ops.ctx, ops.flow, ops)
        res, res_json = neat_get_stats(self.context)
        json_rep = json.loads(res_json)
        shim_print(json.dumps(json_rep, indent=4, sort_keys=True))

        self.local_endpoint = self.crate_and_populate_endpoint()
        self.remote_endpoint = self.crate_and_populate_endpoint(local=False)
        self.state = ConnectionState.ESTABLISHED

        # Protocol stack specific logic
        # Set TCP UTO if enabled
        if self.transport_stack is SupportedProtocolStacks.TCP:
            is_linux = sys.platform == 'linux'
            uto_enabled = self.transport_properties.connection_properties[ConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.USER_TIMEOUT_ENABLED]
            if is_linux and uto_enabled:
                new_timeout = self.transport_properties.connection_properties[ConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.ADVERTISED_USER_TIMEOUT]
                backend.set_timeout(self.context, self.flow, new_timeout)
        if self.message_sent_with_initiate:
            message_data, sent_handler, message_context = self.message_sent_with_initiate
            self.send(message_data, sent_handler=sent_handler, message_context=message_context)

    def crate_and_populate_endpoint(self, local=True):
        if local:
            ret = LocalEndpoint()
            local_ip = backend.get_backend_prop(self.context, self.flow, backend.BackendProperties.LOCAL_IP)
            if local_ip:
                ret.with_address(local_ip)
            else:
                address = backend.get_backend_prop(self.context, self.flow, backend.BackendProperties.ADDRESS)
                if address: ret.with_address(address)

            interface = backend.get_backend_prop(self.context, self.flow, backend.BackendProperties.INTERFACE)
            if interface: ret.with_interface(interface)

            port = backend.get_backend_prop(self.context, self.flow, backend.BackendProperties.PORT)
            if port: ret.with_port(port)
            return ret
        else:
            ret = RemoteEndpoint()
            hostname = backend.get_backend_prop(self.context, self.flow, backend.BackendProperties.DOMAIN_NAME)
            if hostname: ret.with_hostname(hostname)
            remote_ip = backend.get_backend_prop(self.context, self.flow, backend.BackendProperties.REMOTE_IP)
            if remote_ip: ret.with_address(remote_ip)
            return ret

    def set_connection_properties(self):
        try:
            (max_send, max_recv) = neat_get_max_buffer_sizes(self.flow)
            self.transport_properties.connection_properties[ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND] = max_send
            self.transport_properties.connection_properties[ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE] = max_recv

            shim_print(f"Send buffer: {self.transport_properties.connection_properties[ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND]} - Receive buffer: {self.transport_properties.connection_properties[ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE]}")
        except:
            shim_print("An error occurred in the Python callback: {} - {}".format(sys.exc_info()[0], inspect.currentframe().f_code.co_name), level='error')

    def set_property(self, connection_property: ConnectionProperties, value):
        """The application can set and query Connection Properties on a per-Connection basis.
        Connection Properties that are not read-only can be set during pre-establishment (see :py:class:`connection_properties`)
        , as well as on connections directly using the SetProperty action:

        :param connection_property:
            The property to assign a value.
        :param value:
            The value to assign the property.
        """
        # If the connection is part of a connection group set the property for all of the entangled connections
        if self.connection_group:
            for connection in self.connection_group:
                ConnectionProperties.set_property(connection.transport_properties.connection_properties, connection_property, value)
        # Then set the property for the given connection
        ConnectionProperties.set_property(self.transport_properties.connection_properties, connection_property, value)

    def send(self, message_data: bytearray, sent_handler=None, message_context: MessageContext = None, end_of_message: bool = True) -> None:
        """Data is sent as Messages, which allow the application to communicate the boundaries of the data being
        transferred. By default, Send enqueues a complete Message, and takes optional per-:py:class:`message_properties`.
        All Send actions are asynchronous, and deliver events (see Section 7.3). Sending partial Messages for streaming
        large data is also supported

        :param message_data: The data to send
        :param sent_handler: A function that is called after completion / error.
        :param message_context:
        :param end_of_message: When set to false indicates a partial send.
            All data sent with the same MessageContext object will be treated as belonging to the same Message, and will constitute an in-order series until the endOfMessage is marked.
        """
        shim_print("SEND CALLED")

        if self.state == ConnectionState.ESTABLISHING:
            self.message_sent_with_initiate = (message_data, sent_handler, message_context)
            return

        if not message_context:
            message_context = MessageContext()
            message_context.props = self.transport_properties.message_properties

        # If the connection is closed, further sending will result in an SendError
        if self.close_called:
            shim_print(f"SendError - {SendErrorReason.CONNECTION_CLOSING.value}")
            sent_handler(message_context, SendErrorReason.CONNECTION_CLOSING)
            return

        # "If another Message is sent after a Message marked as Final has already been sent on a Connection
        #  the Send Action for the new Message will cause a SendError Event"
        if self.final_message_passed:
            shim_print(f"Send error - {SendErrorReason.FINAL_MESSAGE_PASSED.value}", level='error')
            sent_handler(message_context, SendErrorReason.FINAL_MESSAGE_PASSED)
            return

        # Check for inconsistency between message properties and the connection's transport properties
        inconsistencies = self.check_message_properties(message_context.props)

        if inconsistencies:
            shim_print(f"SendError - {SendErrorReason.INCONSISTENT_PROPERTIES_PASSED.value}:", level='error',
                       additional_msg=inconsistencies)
            sent_handler(message_context, SendErrorReason.INCONSISTENT_PROPERTIES_PASSED)
            return

        if self.message_framer:
            self.message_framer.dispatch_new_sent_message(self, message_data, message_context, sent_handler, end_of_message)
        else:
            self.add_to_message_queue(message_context, message_data, sent_handler, end_of_message)

    def add_to_message_queue(self, message_context, message_data, sent_handler, end_of_message):
        # Check if lifetime is set
        expired_epoch = None
        if message_context.props[MessageProperties.LIFETIME] < math.inf:
            expired_epoch = int(time.time()) + message_context.props[MessageProperties.LIFETIME]
            shim_print(f"Send Actions expires {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expired_epoch))}")
        # "A final message must always be sorted to the end of the list"
        if message_context.props[MessageProperties.FINAL]:
            priority = math.inf
            self.final_message_passed = True
        else:
            priority = -message_context.props[MessageProperties.PRIORITY]
        if self.batch_in_session:
            # Check if batch_struct is already present (i.e if this is the first send in batch or not)
            if isinstance(self.msg_list[-1], List):
                self.msg_list[-1].append(message_data, message_context) # TODO: Remember handler
            else:
                self.msg_list.append([message_data, message_context])   # TODO: Remember handler
        else:
            item = MessageQueueObject(priority, (message_data, message_context, sent_handler, expired_epoch))
            self.msg_list.put(item)
        message_passed(self.ops)

    def receive(self, handler, min_incomplete_length=None, max_length=math.inf) -> None:
        """ As with sending, data is received in terms of Messages. Receiving is an asynchronous operation,
        in which each call to Receive enqueues a request to receive new data from the connection. Once data has been
        received, or an error is encountered, an event will be delivered to complete the Receive request

        :param handler: The function to handle the event delivered during completion
        :param min_incomplete_length:
        :param max_length:
        """
        shim_print("RECEIVED CALLED")

        if self.partitioned_message_data_object:
            if self.partitioned_message_data_object.length > max_length:
                new_partitioned_message_object = self.partitioned_message_data_object.partition(max_length)
                to_be_sent = self.partitioned_message_data_object
                self.partitioned_message_data_object = new_partitioned_message_object
                handler(self, to_be_sent, False, None)
            else:
                to_be_sent = self.partitioned_message_data_object
                self.partitioned_message_data_object = None
                handler(self, to_be_sent, True, None)
        else:
            if self.close_called:
                shim_print("Closed is called, no further reception is possible")
                return
            self.receive_request_queue.append((handler, min_incomplete_length, max_length))
            # If there is only one request in the queue, this means it was empty and we need to set callback
            if len(self.receive_request_queue) is 1:
                received_called(self.ops)

    def batch(self, bacth_block: Callable[[], None]):
        """Used to send multiple messages without the transport system dispatching messages further down the stack.
        Used to minimize overhead, and as a mechanism for the application to indicate that messages could be coalesced
        when possible.

        :param bacth_block: A function / block of code which calls send multiple times
        """
        self.batch_in_session = True
        bacth_block()
        self.batch_in_session = False

    def close(self):
        """Close terminates a Connection after satisfying all the requirements that were specified regarding
        the delivery of Messages that the application has already given to the transport system. For example,
        if reliable delivery was requested for a Message handed over before calling Close, the transport system
        will ensure that this Message is indeed delivered. If the Remote Endpoint still has data to send, it cannot
        be received after this call
        """
        # Check if there is any messages left to pass to NEAT or messages that is not given to the network layer
        if self.msg_list.empty() or self.messages_passed_to_back_end:
            self.close_called = True
            self.state = ConnectionState.CLOSING
        else:
            neat_close(self.ops.ctx, self.ops.flow)
            self.state = ConnectionState.CLOSED

    def abort(self):
        """Abort terminates a Connection without delivering remaining data:
        """
        backend.abort(self.context, self.flow)

    def stop_listener(self):
        self.listener.stop()

    def can_be_used_for_sending(self):
        ret = True
        if self.transport_properties.selection_properties[SelectionProperties.DIRECTION] is CommunicationDirections.UNIDIRECTIONAL_RECEIVE:
            ret = False
        elif self.final_message_received:
            ret = False
        # If close is called on the connection?
        return ret

    def can_be_used_for_receive_data(self):
        ret = True
        if self.transport_properties.selection_properties[SelectionProperties.DIRECTION] is CommunicationDirections.UNIDIRECTIONAL_SEND:
            ret = False
        elif self.final_message_received:
            ret = False
        # If close is called on the connection?
        return ret

    def get_properties(self):
        """At any point, the application can query Connection Properties.
        :return: A dictionary with Connection Properties
        """
        return {'state': self.state,
                'send': self.can_be_used_for_sending(),
                'receive': self.can_be_used_for_receive_data(),
                'props': self.transport_properties}


    def clone(self, clone_handler: Callable[[object, object], None]):
        """Calling Clone on a Connection yields a group of two Connections: the parent Connection on which Clone was
        called, and the resulting cloned Connection. These connections are "entangled" with each other, and become part
        of a Connection Group. Calling Clone on any of these two Connections adds a third Connection to the Connection
        Group, and so on. Connections in a Connection Group generally share Connection Properties. However, ¨
        there may be exceptions, such as "Priority (Connection)", see Section 10.1.3. Like all other Properties,
        Priority is copied to the new Connection when calling Clone(), but it is not entangled: Changing Priority on
        one Connection does not change it on the other Connections in the same Connection Group.

        :param clone_handler: A function to handle clone completion
        """
        try:
            shim_print("CLONE")
            flow = neat_new_flow(self.context)
            ops = neat_flow_operations()

            new_connection = Connection(self.preconnection, 'active', parent=self)

            Connection.clone_count += 1
            self.clone_counter += 1
            ops.clone_id = new_connection.connection_id
            ops.parent_id = self.connection_id

            self.clone_callbacks[self.clone_counter] = clone_handler

            ops.on_error = on_clone_error
            ops.on_connected = handle_clone_ready
            neat_set_operations(self.context, flow, ops)
            backend.pass_candidates_to_back_end([self.transport_stack], self.context, flow)

            neat_open(self.context, flow, self.preconnection.remote_endpoint.address,
                      self.preconnection.remote_endpoint.port, None, 0)
            return new_connection

        except:
            shim_print("An error occurred in the Python callback: {} - {}".format(sys.exc_info()[0], inspect.currentframe().f_code.co_name),level='error')
            backend.stop(self.context)

    def add_child(self, child):
        shim_print("ADDING CHILD IN CONNECTION GROUP")
        self.connection_group.append(child)

    def check_message_properties(self, props):
        inconsistencies = ""
        # Check if lifetime is infinite, if so, check if stack provides reliability
        if props[MessageProperties.LIFETIME] == math.inf and SupportedProtocolStacks.get_service_level(self.transport_stack, SelectionProperties.RELIABILITY) < ServiceLevel.OPTIONAL.value:
            inconsistencies += "\n- Protocol stack does not provide a reliable service while message lifetime set to infinity"
        if props[MessageProperties.IDEMPOTENT] is False and SupportedProtocolStacks.get_service_level(self.transport_stack, AdditionalServices.PROTECTION_AGAINST_DUPLICATED_MESSAGES) == ServiceLevel.NOT_PROVIDED.value:
            inconsistencies += "\n- Message property idempotent is disabled while the connection does not protect against duplicated messages"
        if props[MessageProperties.RELIABLE_DATA_TRANSFER] is True and self.transport_properties.selection_properties[SelectionProperties.RELIABILITY] != PreferenceLevel.REQUIRE:
            inconsistencies += "\n- Reliable data transfer for message set to true - Reliability for connection was not enabled for connection"
        if props[MessageProperties.ORDERED] is True and self.transport_properties.selection_properties[SelectionProperties.PRESERVE_ORDER] == PreferenceLevel.PROHIBIT:
            inconsistencies += "\n- Message property 'ordered' is true while connection does not provide preservation of order"
        return inconsistencies


def handle_writable(ops):
    try:
        connection: Connection = Connection.connection_list[ops.connection_id]

        shim_print(f"ON WRITABLE CALLBACK - connection {connection.connection_id}")

        # Socket is writable, write if any messages passed to the transport system
        if not connection.msg_list.empty():
            # Todo: Should we do coalescing of batch sends here?
            message_to_be_sent, context, handler, expired_epoch = connection.msg_list.get().item

            # If lifetime was set, check if send action has expired
            if expired_epoch and expired_epoch < int(time.time()):
                shim_print("""Send action expired: Expired: {} - Now: {}""".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expired_epoch)),
                                                                              time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))), level='error')
                # Todo: Call event handler if present
                return NEAT_OK

            res = backend.write(ops, message_to_be_sent)
            if res:
                if res == NEAT_ERROR_MESSAGE_TOO_BIG:
                    reason = SendErrorReason.MESSAGE_TOO_LARGE
                elif res == NEAT_ERROR_IO:
                    reason = SendErrorReason.FAILURE_UNDERLYING_STACK
                shim_print(f"SendError - {reason.value}")
                handler(context, reason)
                return
            # Keep message until NEAT confirms sending with all_written
            connection.messages_passed_to_back_end.append((message_to_be_sent, context, handler))
        else:
            shim_print("WHAT")
            ops.on_writable = None
            neat_set_operations(ops.ctx, ops.flow, ops)
    except:
        shim_print("An error occurred in the Python callback: {} - {}".format(sys.exc_info()[0], inspect.currentframe().f_code.co_name), level='error')
        backend.stop(ops.ctx)
    return NEAT_OK


def message_passed(ops):
    try:
        ops.on_writable = handle_writable
        neat_set_operations(ops.ctx, ops.flow, ops)
    except:
        shim_print("An error occurred in the Python callback: {} - {}".format(sys.exc_info()[0], inspect.currentframe().f_code.co_name), level='error')
        backend.stop(ops.ctx)
    return NEAT_OK


def received_called(ops):
    try:
        ops.on_readable = handle_readable
        neat_set_operations(ops.ctx, ops.flow, ops)
    except:
        shim_print("An error occurred in the Python callback: {} - {}".format(sys.exc_info()[0], inspect.currentframe().f_code.co_name), level='error')
        backend.stop(ops.ctx)
    return NEAT_OK


def handle_all_written(ops):
    try:
        close = False
        connection = Connection.connection_list[ops.connection_id]
        shim_print(f"ALL WRITTEN - connection {ops.connection_id}")
        message, message_context, handler = connection.messages_passed_to_back_end.pop(0)

        if handler:
            handler(connection)

        if connection.close_called and len(connection.messages_passed_to_back_end) == 0:
            shim_print("All messages passed down to the network layer - calling close")
            close = True
        elif message_context.props[MessageProperties.FINAL] is True:
            shim_print("Message marked final has been completely sent, closing connection / sending FIN")
            close = True
        if close:
            neat_close(connection.__ops.ctx, connection.__ops.flow)
    except:
        shim_print("An error occurred: {}".format(sys.exc_info()[0]))
        backend.stop(ops.ctx)

    return NEAT_OK


def handle_readable(ops):
    try:
        shim_print(ops)
        connection: Connection = Connection.connection_list[ops.connection_id]

        shim_print(f"HANDLE READABLE - connection {connection.connection_id}")

        if connection.receive_request_queue:
            msg = backend.read(ops, connection.receive_buffer_size)
            shim_print(f'Data received from stream: {ops.stream_id}')

            if connection.message_framer:
                if connection.framer_placeholder.earmarked_bytes_missing > 0:
                    connection.framer_placeholder.fill_earmarked_bytes(msg)
                    # Case if more data than unfulfilled message is received?
                else:
                    connection.framer_placeholder.inbound_data = msg
                    connection.message_framer.dispatch_handle_received_data(connection)
            else:
                handler, min_length, max_length = connection.receive_request_queue.pop(0)
                message_data_object = MessageDataObject(msg, len(msg))

                # Create a message context to pass to the receive handler
                message_context = MessageContext()
                message_context.remote_endpoint = connection.remote_endpoint
                message_context.local_endpoint = connection.local_endpoint
                if connection.stack_supports_message_boundary_preservation:
                    # "If an incoming Message is larger than the minimum of this size and
                    # the maximum Message size on receive for the Connection's Protocol Stack,
                    #  it will be delivered via ReceivedPartial events"
                    if len(msg) > min(max_length, connection.transport_properties.connection_properties[ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE]):
                        partition_size = min(max_length, connection.transport_properties.connection_properties[ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE])
                        partitioned_message_data_object = MessageDataObject(partition_size)
                        connection.partitioned_message_data_object = partitioned_message_data_object
                        handler(connection, message_data_object, message_context, False, None)
                    else:
                        handler(connection, message_data_object, message_context, None, None)
                    # Min length does not need to be checked with stacks that deliver complete messages
                    # TODO: Check if there possibly could be scenarios with SCTP where partial messages is delivered
                else:
                    # No message boundary preservation and no framer yields a receive partial event
                    # TODO: Now, a handler must be sent, but should it be possible to pass None, i.e no handler and just discard bytes/message?
                    if connection.buffered_message_data_object:
                        message_data_object.combine_message_data_objects(connection.buffered_message_data_object)
                    if min_length and min_length > message_data_object.length:
                        connection.buffered_message_data_object = message_data_object
                        connection.receive(handler, min_length, max_length)
                    elif max_length < message_data_object.length:
                        # ReceivePartial event - not end of message
                        connection.buffered_message_data_object = None
                        partitioned_message_data_object = message_data_object.partition(max_length)
                        connection.partitioned_message_data_object = partitioned_message_data_object
                        handler(connection, message_data_object, message_context, False, None)
                    else:
                        handler(connection, message_data_object, message_context, True, None)
        else:
            shim_print("READABLE SET TO NONE - receive queue empty", level='error')
            import time; time.sleep(2)
            ops.on_readable = None
            neat_set_operations(ops.ctx, ops.flow, ops)
    except SystemError:
        return NEAT_OK
    except Exception as es:
        shim_print("An error occurred in the Python callback: {}  {} - {}".format(sys.exc_info()[0], es.args, inspect.currentframe().f_code.co_name), level='error')
        backend.stop(ops.ctx)

    return NEAT_OK


def handle_closed(ops):
    try:
        connection: Connection = Connection.connection_list[ops.connection_id]
        shim_print(f"HANDLE CLOSED - connection {ops.connection_id}")

        if connection.HANDLE_STATE_CLOSED:
            connection.HANDLE_STATE_CLOSED(connection)

        # If a Connection becomes finished before a requested Receive action can be satisfied,
        # the implementation should deliver any partial Message content outstanding..."
        if connection.receive_request_queue:
            if connection.buffered_message_data_object:
                handler, min_length, max_length = connection.receive_request_queue.pop(0)
                shim_print("Dispatching received partial as connection is closing and there is buffered data")
                message_context = MessageContext()
                handler(connection, connection.buffered_message_data_object, message_context, True, None)
            # "...or if none is available, an indication that there will be no more received Messages."
            else:
                shim_print(
                    "Connection closed, there will be no more received messages")  # TODO: Should this be thrown as an error (error event?)
        #if connection.connection_type == 'active':  # should check if there is any cloned connections etc...
        #    backend.stop(ops.ctx)
    except:
        shim_print("An error occurred in the Python callback: {} - {}".format(sys.exc_info()[0], inspect.currentframe().f_code.co_name), level='error')
        backend.stop(ops.ctx)
    return NEAT_OK


def on_clone_error(ops):
    shim_print("Clone operation failed at back end", level="error")
    parent = Connection.connection_list[ops.parent_id]
    handler = parent.clone_callbacks[ops.clone_id]
    handler(None, )
    return NEAT_OK


def handle_clone_ready(ops):
    shim_print("CLONE IS READY TO GO BABY!!")

    cloned_connection = Connection.connection_list[ops.clone_id]
    cloned_connection.established_routine(ops)
    parent = Connection.connection_list[ops.parent_id]
    parent.add_child(cloned_connection)

    ops.on_writable = handle_writable
    neat_set_operations(ops.ctx, ops.flow, ops)

    return NEAT_OK




@dataclass
class FramerPlaceholder:
    connection: Connection
    inbound_data: bytearray = bytearray()
    buffered_data: bytearray = bytearray()
    cursor: int = 0
    earmarked_bytes_missing = 0
    saved_message_context = None
    saved_is_end_of_message = None

    def advance(self, length):
        self.inbound_data = self.inbound_data[length::]

    def fill_earmarked_bytes(self, bytes):
        if len(bytes) < self.earmarked_bytes_missing:
            self.buffered_data += bytes
            self.earmarked_bytes_missing -= len(bytes)
        else:
            if len(bytes) > self.earmarked_bytes_missing:
                msg = self.buffered_data + bytes[0:self.earmarked_bytes_missing]
                self.inbound_data += bytes
            else:
                msg = self.buffered_data + bytes
            handler, min_length, max_length = self.connection.receive_request_queue.pop(0)
            message_data_object = MessageDataObject(msg, len(msg))
            handler(self.connection, message_data_object, self.saved_message_context, self.saved_is_end_of_message, None)
            if len(self.inbound_data) > 0:
                self.connection.message_framer.dispatch_handle_received_data(self.connection)


@dataclass(order=True)
class MessageQueueObject:
    priority: int
    item: Any = field(compare=False)


@dataclass()
class SendError:
    description: str


@dataclass()
class ReceiveError:
    description: str


@dataclass()
class MessageDataObject:
    """
    The messageData object provides access to the bytes that were received for a Message, along with the length of the byte array.
    """
    data: bytearray
    length: int

    def combine_message_data_objects(self, other_object):
        self.data += other_object.data
        self.length += other_object.length

    def partition(self, partition_size):
        other_partition = MessageDataObject()
        other_partition.data = self.data[partition_size::]
        other_partition.length = len(other_partition.data)  # This could easily be done in init, but for now leave it

        self.data = self.data[0:partition_size]
        self.length = len(self.data)

        return other_partition


class ConnectionState(Enum):
    ESTABLISHING = auto()
    ESTABLISHED = auto()
    CLOSING = auto()
    CLOSED = auto()


class SendErrorReason(Enum):
    CONNECTION_CLOSING = "Connection is closing, no further sending is possible"
    FINAL_MESSAGE_PASSED = "Message marked final already sent"
    INCONSISTENT_PROPERTIES_PASSED = "Inconsistencies in message properties"
    MESSAGE_TOO_LARGE = "Message is too large for the system to handle, try sendPartial()"
    FAILURE_UNDERLYING_STACK = "Failure occurred in the underlying protocol stack"

Message_queue_object = Tuple[bytes, MessageContext]
Batch_struct = List[Message_queue_object]

