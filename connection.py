# coding=utf-8
# !/usr/bin/env python3
import inspect
import queue
import time
from dataclasses import dataclass, field

from endpoint import LocalEndpoint, RemoteEndpoint
from message_context import *
from neat import *
import sys
import copy
from transport_properties import *

import backend
from utils import *
from typing import Callable, List, Tuple, Any, Optional
#from typeAliases import ReceiveHandlerTypeSignature, SentHandlerTypeSignature

from enumerations import *


class Connection:
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
        self.clone_callbacks = {}
        self.connection_group = []
        self.state_handler: ConnectionStateHandler = None
        self.local_endpoint = None
        self.remote_endpoint = None
        self.stack_supports_message_boundary_preservation = False

        # if this connection is a result from a clone, add parent
        if parent:
            shim_print(f"Connection is a result of cloning - Parent {parent}")
            self.connection_group.append(parent)

        self.close_called = False
        self.batch_in_session = False
        self.final_message_received = False
        self.final_message_passed = False

        self.preconnection = preconnection
        self.listener = listener
        self.transport_properties: TransportProperties = None
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
        self.set_connection_properties()

        # Fire off appropriate event handler (if present)
        if self.state_handler and self.state_handler.HANDLE_STATE_READY:
            self.state_handler.HANDLE_STATE_READY(self)

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
            uto_enabled = self.transport_properties.connection_properties[GenericConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.USER_TIMEOUT_ENABLED]
            if is_linux and uto_enabled:
                new_timeout = self.transport_properties.connection_properties[GenericConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.ADVERTISED_USER_TIMEOUT]
                backend.set_timeout(self.context, self.flow, new_timeout)

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
            self.transport_properties.connection_properties[GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND] = max_send
            self.transport_properties.connection_properties[GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE] = max_recv

            shim_print(f"Send buffer: {self.transport_properties.connection_properties[GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND]} - Receive buffer: {self.transport_properties.connection_properties[GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE]}")
        except:
            shim_print("An error occurred in the Python callback: {} - {}".format(sys.exc_info()[0], inspect.currentframe().f_code.co_name), level='error')

    def set_property(self, connection_property: GenericConnectionProperties, value):
        # If the connection is part of a connection group set the property for all of the entangled connections
        if self.connection_group:
            for connection in self.connection_group:
                GenericConnectionProperties.set_property(connection.transport_properties.connection_properties, connection_property, value)
        # Then set the property for the given connection
        GenericConnectionProperties.set_property(self.transport_properties.connection_properties, connection_property, value)

    def send(self, message_data, sent_handler=None, message_context=None, end_of_message=True):
        shim_print("SEND CALLED")

        if not message_context:
            message_context = MessageContext()
            message_context.props = self.transport_properties.message_properties

        # If the connection is closed, further sending will result in an SendError
        if self.close_called:
            shim_print("SendError - Closed is called, no further sending is possible")
            return

        # "If another Message is sent after a Message marked as Final has already been sent on a Connection
        #  the Send Action for the new Message will cause a SendError Event"
        if self.final_message_passed:
            shim_print("Send error - Message marked final already sent", level='error')

        # Check for inconsistency between message properties and the connection's transport properties
        inconsistencies = self.check_message_properties(message_context.props)

        if inconsistencies:
            shim_print(f"SendError - inconsistencies in message properties:", level='error',
                       additional_msg=inconsistencies)
            return

        # Check if lifetime is set
        expired_epoch = None
        if message_context.props[MessageProperties.LIFETIME] < math.inf:
            expired_epoch = int(time.time()) + message_context.props[MessageProperties.LIFETIME]
            shim_print(f"Send Actions expires {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expired_epoch))}")

        # "A final message must always be sorted to the end of the list
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

    def receive(self, handler, min_incomplete_length=None, max_length=math.inf):
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
        self.batch_in_session = True
        bacth_block()
        self.batch_in_session = False

    def close(self):
        # Check if there is any messages left to pass to NEAT or messages that is not given to the network layer
        if self.msg_list.empty() or self.messages_passed_to_back_end:
            self.close_called = True
            self.state = ConnectionState.CLOSING
        else:
            neat_close(self.ops.ctx, self.ops.flow)
            self.state = ConnectionState.CLOSED

    def abort(self):
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
        return {'state': self.state,
                'send': self.can_be_used_for_sending(),
                'receive': self.can_be_used_for_receive_data(),
                'props': self.transport_properties}

    def clone(self, clone_handler: Callable[[object, object], None]):
        try:
            shim_print("CLONE")
            flow = neat_new_flow(self.context)
            ops = neat_flow_operations()

            Connection.clone_count += 1
            self.clone_counter += 1
            ops.clone_id = self.clone_counter
            ops.parent_id = self.connection_id

            self.clone_callbacks[self.clone_counter] = clone_handler

            ops.on_error = on_clone_error
            ops.on_connected = handle_clone_ready
            neat_set_operations(self.context, flow, ops)
            backend.pass_candidates_to_back_end([self.transport_stack], self.context, flow)

            neat_open(self.context, flow, self.preconnection.remote_endpoint.address,
                      self.preconnection.remote_endpoint.port, None, 0)
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
                    reason = "The message is too large for the system to handle"
                elif res == NEAT_ERROR_IO:
                    reason = "Failure of processing message in the protocol stack"
                shim_print(f"SendError - Neat failed while writing - {reason}")
                # Todo: Elegant error handling
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

        if connection.close_called and len(connection.messages_passed_to_back_end) == 0:
            shim_print("All messages passed down to the network layer - calling close")
            close = True
        elif message_context.props[MessageProperties.FINAL] is True:
            shim_print("Message marked final has been completely sent, closing connection / sending FIN")
            close = True
        if close:
            neat_close(connection.__ops.ctx, connection.__ops.flow)

        if handler:
            handler(connection)

    except:
        shim_print("An error occurred: {}".format(sys.exc_info()[0]))
        backend.stop(ops.ctx)

    return NEAT_OK


def handle_readable(ops):
    try:
        connection: Connection = Connection.connection_list[ops.connection_id]
        shim_print(f"HANDLE READABLE - connection {connection.connection_id}")

        if connection.receive_request_queue:
            handler, min_length, max_length = connection.receive_request_queue.pop(0)
            msg = backend.read(ops, connection.receive_buffer_size)
            message_data_object = MessageDataObject(msg, len(msg))

            shim_print(f'Message received from stream: {ops.stream_id}')

            # Create a message context to pass to the receive handler
            message_context = MessageContext()
            message_context.remote_endpoint = connection.remote_endpoint
            message_context.local_endpoint = connection.local_endpoint

            if connection.stack_supports_message_boundary_preservation:
                # "If an incoming Message is larger than the minimum of this size and
                # the maximum Message size on receive for the Connection's Protocol Stack,
                #  it will be delivered via ReceivedPartial events"
                if len(msg) > min(max_length, connection.transport_properties.connection_properties[GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE]):
                    partition_size = min(max_length, connection.transport_properties.connection_properties[GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE])
                    partitioned_message_data_object = MessageDataObject(partition_size)
                    connection.partitioned_message_data_object = partitioned_message_data_object
                    handler(connection, message_data_object, message_data_object, False, None)
                else:
                    handler(connection, message_data_object, message_context, None, None)
                # Min length does not need to be checked with stacks that deliver complete messages
                # TODO: Check if there possibly could be scenarios with SCTP where partial messages is delivered
            else:
                # If a framer, pass the message
                if False:
                    NotImplementedError
                # No message boundary preservation and no framer yields a receive partial event
                else:
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
        connection = Connection.connection_list[ops.connection_id]
        shim_print(f"HANDLE CLOSED - connection {ops.connection_id}")

        # TODO: Check if state handler has closed handler

        # If a Connection becomes finished before a requested Receive action can be satisfied,
        # the implementation should deliver any partial Message content outstanding..."
        if connection.receive_request_queue:
            if connection.tcp_to_small_queue:
                handler = connection.receive_request_queue.pop(0)[
                    0]  # Should check if there is more than one request in the queue
                shim_print("Sending leftovers")
                message_context = MessageContext()
                handler(connection, connection.tcp_to_small_queue.pop(), message_context)
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

    parent = Connection.connection_list[ops.parent_id]
    cloned_connection = Connection(parent.preconnection, 'active', parent=parent)
    cloned_connection.established_routine(ops)
    parent.add_child(cloned_connection)

    ops.on_writable = handle_writable
    neat_set_operations(ops.ctx, ops.flow, ops)

    handler = parent.clone_callbacks[ops.clone_id]
    handler(cloned_connection, None)
    return NEAT_OK


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
        excess_object = MessageDataObject()
        excess_object.data = self.data[partition_size::]
        excess_object.length = len(excess_object.data)  # This could easily be done in init, but for now leave it

        self.data = self.data[0:partition_size]
        self.length = len(self.data)

        return excess_object




class ConnectionState(Enum):
    ESTABLISHING = auto()
    ESTABLISHED = auto()
    CLOSING = auto()
    CLOSED = auto()


@dataclass()
class ConnectionStateHandler:
    HANDLE_STATE_READY: Callable[[], None] = None  # Connection to be passed, if no design change?
    HANDLE_STATE_CLOSED: Callable[[], None] = None
    HANDLE_STATE_CONNECTION_ERROR: Callable[[], None] = None


Message_queue_object = Tuple[bytes, MessageContext]
Batch_struct = List[Message_queue_object]

