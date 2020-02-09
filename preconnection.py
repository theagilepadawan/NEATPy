# coding=utf-8

from neat import *
from connection import *
from listener import *
from utils import *
from endpoint import *
import backend
from enumerations import *
import sys


class Preconnection:
    preconnection_list = {}
    listener_list = {}

    def __init__(self, local_endpoint=None, remote_endpoint=None,
                 transport_properties=None, security_parameters=None):

        self.__context, self.__flow, self.__ops = backend.bootstrap_backend()

        # Todo: Find a more sophisticated way to keep track of preconnections
        Preconnection.preconnection_list[0] = self

        # ...event handlers to be registered by the application
        self.local_endpoint = local_endpoint
        self.remote_endpoint: RemoteEndpoint = remote_endpoint
        self.transport_properties = transport_properties
        self.number_of_connections = 0  # Is this really needed for the preconnecntion? Maybe regarding rendezvous?
        self.connection_limit = None
        self.framer_list = []

        self.event_handler_list = {event: None for name, event in ConnectionEvents.__members__.items()}
        self.transport_properties = transport_properties
        if not self.transport_properties:
            self.transport_properties = TransportProperties()

    def set_event_handler(self, event: ConnectionEvents, handler):
        if isinstance(event, ConnectionEvents):
            self.event_handler_list[event] = handler
        else:
            shim_print("No valid event passed. Ignoring")

    """
    []
    Active open is the Action of establishing a Connection to a Remote Endpoint presumed to be listening for incoming
    Connection requests. Active open is used by clients in client-server interactions.
    """

    def initiate(self):
        if not self.remote_endpoint:
            shim_print("Initiate error - Remote Endpoint MUST be specified if when calling initiate on the preconnection", level="error")
            backend.clean_up(self.__context)
            sys.exit(1)

        def on_initiate_error(ops):
            shim_print("Initiate error - Unable to connect to remote endpoint", level="error")
            backend.stop(self.__context)
            return NEAT_OK

        self.__ops.on_error = on_initiate_error
        self.__ops.on_connected = self.client_on_connected
        neat_set_operations(self.__context, self.__flow, self.__ops)

        candidates = self.transport_properties.select_protocol_stacks_with_selection_properties()

        if candidates is None:
            # "An InitiateError occurs either when the set of transport properties and security
            #  parameters cannot be fulfilled on a connection
            shim_print("Initiate error - No stacks meeting the given constraints by properties", level="error")
            # Todo: call eventual event handler
            return

        backend.pass_candidates_to_back_end(candidates, self.__context, self.__flow)
        if backend.initiate(self.__context, self.__flow, self.remote_endpoint.address, self.remote_endpoint.port, 100):
            ""
        backend.start(self.__context)
        backend.clean_up(self.__context)

    """
    []
    Passive open is the Action of waiting for Connections from remote Endpoints, commonly used by servers in
    client-server interactions. Passive open is supported by this interface through the Listen Action and returns a
    Listener object:
    """
    def listen(self):
        if not self.local_endpoint:
            shim_print("Initiate error - Local Endpoint MUST be specified if when calling listen on the preconnection", level="error")
            backend.clean_up(self.__context)
            sys.exit(1)

        candidates = self.transport_properties.select_protocol_stacks_with_selection_properties()
        if candidates is None:
            # "An InitiateError occurs either when the set of transport properties and security
            #  parameters cannot be fulfilled on a connection
            shim_print("Initiate error - No stacks meeting the given constraints by properties", level="error")
            # Todo: call eventual event handler
            return

        backend.pass_candidates_to_back_end(candidates, self.__context, self.__flow)
        shim_print("LISTEN!")
        listner = Listener(self.__context, self.__flow, self.__ops, self)
        return NEAT_OK

    """
    []
    The Rendezvous() Action causes the Preconnection to listen on the Local Endpoint for an incoming Connection from
    the Remote Endpoint, while simultaneously trying to establish a Connection from the Local Endpoint to the Remote Endpoint.
    """
    def rendezvous(self):
        additional_ctx, additional_flow, additional_ops = backend.bootstrap_backend()

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

    def add_framer(self, framer):
        self.framer_list.append(framer)

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
