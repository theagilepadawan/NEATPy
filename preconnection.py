# coding=utf-8

from neat import *
from connection import Connection
from listener import *
from utils import *
import neat_utils
from enumerations import *
import sys


class Preconnection:
    preconnection_list = {}
    listener_list = {}

    def __init__(self, local_endpoint=None, remote_endpoint=None,
                 transport_properties=None,
                 security_parameters=None):

        self.__context, self.__flow, self.__ops = neat_utils.neat_bootstrap()

        # Todo: Find a more sophisticated way to keep track of preconnections
        Preconnection.preconnection_list[0] = self

        # ...event handlers to be registered by the application
        self.ready_handler = None
        self.receive_handler = None
        self.sent_handler = None

        self.local_endpoint = local_endpoint
        self.remote_endpoint = remote_endpoint
        self.transport_properties = transport_properties
        self.number_of_connections = 0
        self.connection_limit = None

        self.event_handler_list = {event: None for name, event in ConnectionEvents.__members__.items()}

        if self.transport_properties is not None:
            json_representation = self.transport_properties.to_json()
            if json_representation is None:
                shim_print("No protocols support given properties")
                exit(1)
            shim_print(json_representation)
            neat_set_property(self.__context, self.__flow, json_representation)
        return

    def set_event_handler(self, event: ConnectionEvents, handler):
        if isinstance(event, ConnectionEvents):
            self.event_handler_list[event] = handler
        else:
            shim_print("No valid event passed. Exiting.")
            sys.exit(1)

    """
    []
    Active open is the Action of establishing a Connection to a Remote Endpoint presumed to be listening for incoming 
    Connection requests. Active open is used by clients in client-server interactions.
    """

    def initiate(self):
        if not self.remote_endpoint:
            shim_print("Remote Endpoint MUST be specified if when calling initiate on the preconnection")
            sys.exit(1)

        self.__ops.on_connected = self.client_on_connected
        neat_set_operations(self.__context, self.__flow, self.__ops)

        if neat_open(self.__context, self.__flow, self.remote_endpoint.address, self.remote_endpoint.port, None, 0):
            # Todo: should this just return None to application?
            sys.exit("neat_open failed")

        shim_print("CLIENT RUNNING NEAT INITIATED FROM PYTHON")

        neat_start_event_loop(self.__context, NEAT_RUN_DEFAULT)
        # neat_free_ctx(self.ctx)
        return

    """
    []
    Passive open is the Action of waiting for Connections from remote Endpoints, commonly used by servers in 
    client-server interactions. Passive open is supported by this interface through the Listen Action and returns a 
    Listener object:
    """

    def listen(self):
        if not self.local_endpoint  :
            shim_print("Local Endpoint MUST be specified if when calling listen on the preconnection")
            sys.exit(1)

        shim_print("LISTEN!")
        listner = Listener(self.__context, self.__flow, self.__ops, self)
        return

    """
    []
    The Rendezvous() Action causes the Preconnection to listen on the Local Endpoint for an incoming Connection from 
    the Remote Endpoint, while simultaneously trying to establish a Connection from the Local Endpoint to the Remote Endpoint.
    """

    def rendezvous(self):
        additional_ctx, additional_flow, additional_ops = neat_utils.neat_bootstrap()

        self.__ops.on_connected = self.handle_connected_rendezvous
        neat_set_operations(self.__context, self.__flow, self.__ops)

        additional_ops.on_connected = self.handle_connected_rendezvous
        neat_set_operations(additional_ctx, additional_flow, additional_ops)

        if self.local_endpoint is None or self.remote_endpoint is None:
            shim_print("Both local and remote endpoints must be set for rendezvous. Aborting...")
            sys.exit(1)

        if neat_open(self.__context, self.__flow, self.remote_endpoint.address, self.remote_endpoint.port, None, 0):
            # Todo: should this just return None to application?
            sys.exit("neat_open failed")

        if neat_accept(additional_ctx, additional_flow, self.local_endpoint.port, None, 0):
            sys.exit("neat_accept failed")

        shim_print("Rendezvous started! 🤩")

    @staticmethod
    def handle_connected_rendezvous(ops):
        precon = Preconnection.preconnection_list[0]
        precon.number_of_connections += 1
        new_connection = Connection(ops, precon, 'rendezvous')
        return NEAT_OK

    @staticmethod
    def client_on_connected(ops):
        shim_print("ON CONNECTED RAN (CLIENT)")
        precon = Preconnection.preconnection_list[0]
        precon.number_of_connections += 1
        new_connection = Connection(ops, precon, 'active')
        return NEAT_OK
