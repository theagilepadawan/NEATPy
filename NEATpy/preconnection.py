# coding=utf-8
import json
from enum import Enum
from typing import Callable
from connection import Connection
from endpoint import RemoteEndpoint
from listener import Listener
from message_context import MessageContext
from message_framer import MessageFramer
from neat import *
import backend
import sys
from transport_properties import TransportProperties
from utils import shim_print


class Preconnection:
    preconnection_list = {}
    initiated_connection_list = {}
    preconnection_counter = 1

    def __init__(self, local_endpoint=None, remote_endpoint=None, transport_properties=None, security_needed: bool = False, unfulfilled_handler=None):
        """ A Preconnection represents a set of properties and constraints on the selection and configuration of paths
        and protocols to establish a Connection with a remote Endpoint.

        :param local_endpoint:
            Optional local endpoint to be used with the preconnection
        :param remote_endpoint:
            Optional remote endpoint to be used with the preconnection
        :param transport_properties:
            A transport property object with desired selection properties.
        :param security_needed: Indicated whether or not a secure connection is needed.
        :param unfulfilled_handler:
            A function handling an unfulfilled error
        """
        # NEAT bootstrap
        self.__context, self.__flow, self.__ops = backend.bootstrap_backend()

        self.security_parameteres = security_needed
        self.unfulfilled_handler = unfulfilled_handler
        self.number_of_connections = 0
        self.connection_limit = None
        self.message_framer = None

        # Set ID, to be used in NEAT callbacks to identify the Preconnection
        self.id = Preconnection.preconnection_counter
        self.__ops.preconnection_id = self.id
        Preconnection.preconnection_counter += 1
        Preconnection.preconnection_list[self.id] = self

        self.local_endpoint = local_endpoint
        self.remote_endpoint: RemoteEndpoint = remote_endpoint
        self.transport_properties = transport_properties
        if not self.transport_properties:
            self.transport_properties = TransportProperties()

        if transport_properties.buffer_capacity:
            transport_properties.dispatch_capacity_profile(self.__context, self.__flow)
            transport_properties.buffer_capacity = None


    def initiate(self, timeout=None) -> Connection:
        """ Initiate (Active open) is the Action of establishing a Connection to a Remote Endpoint presumed to be listening for incoming
        Connection requests. Active open is used by clients in client-server interactions. Note that start() must be
        called on the preconnection.

        :param timeout:
            The timeout parameter specifies how long to wait before aborting Active open.
        """
        if not self.remote_endpoint:
            shim_print("Initiate error - Remote Endpoint MUST be specified if when calling initiate on the preconnection", level="error")
            backend.clean_up(self.__context)
            sys.exit(1)

        self.__ops.on_error = self.on_initiate_error
        self.__ops.on_timeout = self.on_initiate_timeout
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

        if self.security_parameteres:
            self.register_security()

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

    def initiate_with_send(self, message_data, sent_handler, message_context=None, timeout=None) -> Connection:
        """For application-layer protocols where the Connection initiator also sends the first message,
        the InitiateWithSend() action combines Connection initiation with a first Message sent.
        Returns a Connection object in the ``establishing`` state.

        :param message_data: The message to be sent
        :param sent_handler: A function / completion handler, handling both a successful completion and errors.
        :param message_context: Optional, used to indicate the message is idempotent, so it possibly can be used with
               0-RTT establishment, if supported by the transport stack and system.
        :param timeout: The timeout parameter specifies how long to wait before aborting Active open.
        """
        new_connection = self.initiate(timeout=timeout)
        new_connection.send(message_data, sent_handler=sent_handler, message_context=message_context)
        return new_connection

    def start(self):
        """ Starts the transport systems. Must be called after initiate / listen.

        :return: This function does not return.
        """
        backend.start(self.__context)
        backend.clean_up(self.__context)

    def listen(self):
        """Listen (Passive open) is the Action of waiting for Connections from remote Endpoints. Before listening
        the transport system will resolve transport properties for candidate protocol stacks. A local endpoint must be
        passed to the preconnection prior to listen.

        :return: A listener object.
        """
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

        if self.security_parameteres:
            self.register_security(is_server=True)

        shim_print("LISTEN!")
        listener = Listener(self.__context, self.__flow, self.__ops, self)
        return listener

    def add_framer(self, framer):
        """ Adds a framer to the Preconnection to run on top of transport protocols. Multiple Framers may be added.
        If multiple Framers are added, the last one added runs first when framing outbound messages, and last when
        parsing inbound data.

        :param framer: The framer to be added. Must inherit from the :py:class:`framer` class and implement its abstract functions.
        """
        if self.message_framer:
            self.message_framer.append_framer(framer)
        else:
            self.message_framer = MessageFramer(framer)

    def register_security(self, is_server=None):
        if is_server:
            neat_secure_identity(self.__context, self.__flow, "/Users/michael/Skole/Master/neat/examples/cert.pem", NEAT_CERT_KEY_PEM)
        sec = json.dumps({"security": {"value": True, "precedence": 2}})
        neat_set_property(self.__context, self.__flow, sec)
        ver = json.dumps({"verification": {"value": False, "precedence": 2}})
        neat_set_property(self.__context, self.__flow, ver)

    @staticmethod
    def client_on_connected(ops):
        shim_print("ON CONNECTED RAN (CLIENT)")
        precon: Preconnection = Preconnection.preconnection_list[ops.preconnection_id]
        precon.number_of_connections += 1
        con: Connection = Preconnection.initiated_connection_list[ops.preconnection_id]
        con.established_routine(ops)
        return NEAT_OK

    @staticmethod
    def on_initiate_error(ops):
        shim_print("Initiate error - Unable to connect to remote endpoint", level="error")
        backend.stop(ops.ctx)
        return NEAT_OK

    @staticmethod
    def on_initiate_timeout(ops):
        shim_print("Timeout - aborting Active open", level="error")
        backend.stop(ops.ctx)
        return NEAT_OK
