import copy
import sys

import backend
import math;
from neat import *
from connection import *
from utils import *


@dataclass()
class ListenerStateHandler:
    HANDLE_STATE_LISTENING: Callable[[], None] = None
    HANDLE_STATE_LISTEN_ERROR: Callable[[], None] = None
    HANDLE_STATE_STOPPED: Callable[[], None] = None
    HANDLE_CONNECTION_RECEIVED: Callable[[Connection], None] = None


class ListenErrorReasons(Enum):
    UNFULFILLED_PROPERTIES = 'Properties of the preconnection cannot be fulfilled for listening'
    UNRESOLVED_LOCAL_ENDPOINT = 'The Local Endpoint cannot be resolved'
    PROHIBITED_BY_POLICY = 'Listening is prohibited by policy'


class Listener:
    listener_list = {}

    def __init__(self, context, flow, ops, preconnection):
        self.__ops: neat_flow_operations = ops
        self.__context = context
        self.__flow = flow

        self.preconnection = preconnection
        self.props = copy.deepcopy(preconnection.transport_properties)
        self.number_of_connections = 0
        self.connection_limit = math.inf
        self.state_handler: ListenerStateHandler = None

        # Todo: Find a more sophisticated way to keep track of listeners (or is it necessary?)
        Listener.listener_list[0] = self

        self.__ops.on_connected = self.handle_connected
        self.__ops.on_readable = handle_readable
        self.__ops.on_error = self.handle_error

        neat_set_operations(self.__context, self.__flow, self.__ops)

        if neat_accept(self.__context, self.__flow, preconnection.local_endpoint.port, None, 0):
            sys.exit("neat_accept failed")

        shim_print("A SERVER RUNNING NEAT STARTING FROM PYTHON 🎊")

    def stop(self):
        shim_print("LISTENER STOP")
        if self.state_handler and self.state_handler.HANDLE_STATE_STOPPED:
            self.state_handler.HANDLE_STATE_STOPPED()
        backend.stop(self.__context)

    def set_new_connection_limit(self, value):
        self.connection_limit = value

    def reset_connection_limit(self):
        self.connection_limit = math.inf

    @staticmethod
    def handle_error(ops):
        listener: Listener = Listener.listener_list[0]
        shim_print(f"Listner error - {ListenErrorReasons.UNRESOLVED_LOCAL_ENDPOINT.value}")
        if listener.state_handler and listener.state_handler.HANDLE_STATE_LISTEN_ERROR:
            listener.state_handler.HANDLE_STATE_LISTEN_ERROR(ListenErrorReasons.UNRESOLVED_LOCAL_ENDPOINT)
        listener.stop()

    @staticmethod
    def handle_connected(ops):
        listener = Listener.listener_list[0]
        if listener.connection_limit > listener.number_of_connections:
            listener.number_of_connections += 1

            new_connection = Connection(listener.preconnection, 'passive', listener)
            new_connection.established_routine(ops)

            if listener.state_handler and listener.state_handler.HANDLE_CONNECTION_RECEIVED:
                listener.state_handler.HANDLE_CONNECTION_RECEIVED(new_connection)
        else:
            shim_print("Connection limit is reached!")

        return NEAT_OK
