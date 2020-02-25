# coding=utf-8
import threading

from neat import *
from connection import *
from listener import *
from utils import *
from endpoint import *
import backend
from enumerations import *
import sys


class RendezvousObject:

    def __init__(self, context, initiate_id, listen_id, initiate_flow, listen_flow, handler):
        self.context = context
        self.initiate_id = initiate_id
        self.listen_id = listen_id
        self.initiate_flow = initiate_flow
        self.listen_flow = listen_flow
        self.rendezvous_completion_handler: Callable[[Connection, MessageContext, RendezvousErrorReasons], None] = handler

    def mark_connected(self, connected_id):
        shim_print("Aborting the other flow in rendezvous")
        if connected_id == self.initiate_id:
            abort_flow = self.listen_flow
        else:
            abort_flow = self.initiate_flow
        neat_abort(self.context, abort_flow)


class RendezvousErrorReasons(Enum):
    LOCAL_ENDPOINT_NOT_RESOLVED = 'Local endpoint cannot be resolved'
    REMOTE_ENDPOINT_NOT_RESOLVED = 'Remote endpoint cannot be resolved'
    POLICY_PROHIBIT_RENDEZVOUS = 'Application is prohibited from rendezvous by policy'
    ENDPOINT_UNREACHABLE = 'No transport-layer connection can be established to remote endpoint'
    NO_LISTENING = 'Preconnection cannot be fulfilled for listening'


class Preconnection:
    preconnection_list = {}
    listener_list = {}
    initiated_connection_list = {}
    preconnection_counter = 1
    rendezvous_counter = 1

    def __init__(self, local_endpoint=None, remote_endpoint=None,
                 transport_properties=None, security_parameters=None, unfulfilled_handler=None):

        self.__context, self.__flow, self.__ops = backend.bootstrap_backend()
        self.id = Preconnection.preconnection_counter
        self.__ops.preconnection_id = self.id
        Preconnection.preconnection_counter += 1
        Preconnection.preconnection_list[self.id] = self

        # For rendezvous
        self.rendezvous_object: RendezvousObject = None

        # ...event handlers to be registered by the application
        self.local_endpoint = local_endpoint
        self.remote_endpoint: RemoteEndpoint = remote_endpoint
        self.transport_properties = transport_properties
        self.number_of_connections = 0  # Is this really needed for the preconnection? Maybe regarding rendezvous?
        self.connection_limit = None
        self.unfulfilled_handler = unfulfilled_handler
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

    def initiate(self, timeout=None):
        if not self.remote_endpoint:
            shim_print("Initiate error - Remote Endpoint MUST be specified if when calling initiate on the preconnection", level="error")
            backend.clean_up(self.__context)
            sys.exit(1)

        def on_initiate_error(ops):
            shim_print("Initiate error - Unable to connect to remote endpoint", level="error")
            backend.stop(self.__context)
            return NEAT_OK

        def on_initiate_timeout(ops):
            shim_print("Timeout - aborting Active open", level="error")
            backend.stop(self.__context)
            return NEAT_OK

        self.__ops.on_error = on_initiate_error
        self.__ops.on_timeout = on_initiate_timeout
        self.__ops.on_connected = self.client_on_connected
        neat_set_operations(self.__context, self.__flow, self.__ops)

        candidates = self.transport_properties.select_protocol_stacks_with_selection_properties()

        if candidates is None:
            shim_print("Unfulfilled error - No stacks meeting the given constraints by properties", level="error")
            if self.unfulfilled_handler:
                self.unfulfilled_handler()
            else:
                backend.clean_up(self.__context)
            return

        backend.pass_candidates_to_back_end(candidates, self.__context, self.__flow)
        if backend.initiate(self.__context, self.__flow, self.remote_endpoint.address, self.remote_endpoint.port, 100):
            pass
        if timeout:
            set_initiate_timer(self.__context, self.__flow, self.__ops, timeout)

        if self.remote_endpoint.interface:
            send = json.dumps({"interface": {"value": self.remote_endpoint.interface, "precedence": 1}})
            neat_set_property(self.__context, self.__flow, send)

        new_con = Connection(self, 'active')
        Preconnection.initiated_connection_list[self.id] = new_con
        return new_con

    def start(self):
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
            shim_print("Listen error - Local Endpoint MUST be specified if when calling listen on the preconnection", level="error")
            backend.clean_up(self.__context)
            sys.exit(1)

        candidates = self.transport_properties.select_protocol_stacks_with_selection_properties()
        if candidates is None:
            shim_print("Unfulfilled error - No stacks meeting the given constraints by properties", level="error")
            if self.unfulfilled_handler:
                self.unfulfilled_handler()
            else:
                backend.clean_up(self.__context)

        backend.pass_candidates_to_back_end(candidates, self.__context, self.__flow)
        shim_print("LISTEN!")
        listener = Listener(self.__context, self.__flow, self.__ops, self)
        return listener


    """
    []
    The Rendezvous() Action causes the Preconnection to listen on the Local Endpoint for an incoming Connection from
    the Remote Endpoint, while simultaneously trying to establish a Connection from the Local Endpoint to the Remote Endpoint.
    """
    def rendezvous(self, completion_handler: Callable[[Connection, MessageContext, RendezvousErrorReasons], None]):
        # Both local and remote endpoint must be set
        if self.local_endpoint is None or self.remote_endpoint is None:
            shim_print("Both local and remote endpoints must be set for rendezvous. Aborting...", level='error')
            return

        # Create additional flow and operations struct, so that NEAT can do both active and passive open
        additional_flow = neat_new_flow(self.__context)
        additional_ops = neat_flow_operations()

        # Register id for listen flow
        additional_ops.preconnection_id = self.id
        additional_ops.rendezvous_id = Preconnection.rendezvous_counter
        Preconnection.rendezvous_counter += 1

        # Register id for initiate flow
        self.__ops.preconnection_id = self.id
        self.__ops.rendezvous_id = Preconnection.rendezvous_counter
        Preconnection.rendezvous_counter += 1

        # Set callbacks to handle errors and when a connection is established either way
        self.__ops.on_connected = self.handle_connected_rendezvous_initiate
        self.__ops.on_error = self.handle_error_rendezvous_initiate
        neat_set_operations(self.__context, self.__flow, self.__ops)

        additional_ops.on_connected = self.handle_connected_rendezvous_listen
        additional_ops.on_error = self.handle_error_rendezvous_listen
        neat_set_operations(self.__context, additional_flow, additional_ops)

        # Get candidate protocol stacks by handling properties set
        candidates = self.transport_properties.select_protocol_stacks_with_selection_properties()
        candidates2 = self.transport_properties.select_protocol_stacks_with_selection_properties()

        # Return a rendezvous error if there are no candidates
        if candidates is None:
            shim_print("Unfulfilled error - No stacks meeting the given constraints by properties", level="error")
            if self.unfulfilled_handler:
                self.unfulfilled_handler()
            else:
                backend.clean_up(self.__context)

        # Pass candidates to both flows
        backend.pass_candidates_to_back_end(candidates, self.__context, self.__flow)
        backend.pass_candidates_to_back_end(candidates2, self.__context, additional_flow)

        # Open and accept in NEAT
        if neat_open(self.__context, self.__flow, self.remote_endpoint.address, self.remote_endpoint.port, None, 0):
            shim_print("Back-end is out of memory", level='error')
        if neat_accept(self.__context, additional_flow, self.local_endpoint.port, None, 0):
            shim_print("Back-end is out of memory", level='error')

        # Create rendezvous object to be used in callbacks, to stop the flow that is not connected when the first is
        self.rendezvous_object = RendezvousObject(self.__context, self.__ops.rendezvous_id, additional_ops.rendezvous_id, self.__flow, additional_flow, completion_handler)

        shim_print("Rendezvous started! 🤩")
        backend.start(self.__context)
        backend.clean_up(self.__context)

    def add_framer(self, framer):
        self.framer_list.append(framer)

    @staticmethod
    def handle_connected_rendezvous_listen(ops):
        precon: Preconnection = Preconnection.preconnection_list[ops.preconnection_id]
        precon.rendezvous_object.mark_connected(ops.rendezvous_id)
        precon.number_of_connections += 1
        new_con: Connection = Connection(precon, 'passive')
        new_con.established_routine(ops)
        if precon.rendezvous_object.rendezvous_completion_handler:
            precon.rendezvous_object.rendezvous_completion_handler(new_con, None, None)
        # TODO: If this is a connection from the listener, check that the peer is in fact the remote endpoint specified
        return NEAT_OK

    @staticmethod
    def handle_connected_rendezvous_initiate(ops):
        precon: Preconnection = Preconnection.preconnection_list[ops.preconnection_id]
        precon.rendezvous_object.mark_connected(ops.rendezvous_id)
        precon.number_of_connections += 1
        new_con: Connection = Connection(precon, 'active')
        new_con.established_routine(ops)
        if precon.rendezvous_object.rendezvous_completion_handler:
            precon.rendezvous_object.rendezvous_completion_handler(new_con, None, None)
        # TODO: If this is a connection from the listener, check that the peer is in fact the remote endpoint specified
        return NEAT_OK

    @staticmethod
    def handle_error_rendezvous_listen(ops):
        precon: Preconnection = Preconnection.preconnection_list[ops.preconnection_id]
        if precon.rendezvous_object.rendezvous_completion_handler:
            precon.rendezvous_object.rendezvous_completion_handler(None, None, RendezvousErrorReasons.LOCAL_ENDPOINT_NOT_RESOLVED)

        shim_print(f"Rendezvous error - {RendezvousErrorReasons.LOCAL_ENDPOINT_NOT_RESOLVED.value}", level='error')
        return NEAT_OK

    @staticmethod
    def handle_error_rendezvous_initiate(ops):
        precon: Preconnection = Preconnection.preconnection_list[ops.preconnection_id]
        if precon.rendezvous_object.rendezvous_completion_handler:
            precon.rendezvous_object.rendezvous_completion_handler(None, None, RendezvousErrorReasons.REMOTE_ENDPOINT_NOT_RESOLVED)

        shim_print(f"Rendezvous error - {RendezvousErrorReasons.REMOTE_ENDPOINT_NOT_RESOLVED.value}", level='error')
        return NEAT_OK

    @staticmethod
    def client_on_connected(ops):
        shim_print("ON CONNECTED RAN (CLIENT)")
        precon: Preconnection = Preconnection.preconnection_list[ops.preconnection_id]
        precon.number_of_connections += 1
        con: Connection = Preconnection.initiated_connection_list[ops.preconnection_id]
        con.established_routine(ops)
        return NEAT_OK

