# coding=utf-8

from neat import *
from connection import Connection
from listener import *
from utils import *
import neat_utils
from callbacks import *
import sys


class Preconnection:
    preconnection_list = {}
    listner_list = {}

    def __init__(self, local_endpoint=None, remote_endpoint=None,
                 transport_properties=None,
                 security_parameters=None):

        self.__context, self.__flow, self.__ops = neat_utils.neat_bootstrap()

        # Todo: Find a more sophisticated way to keep track of preconnections
        Preconnection.preconnection_list[0] = self

        # ..."event handlers to be registered by the application
        self.ready_handler = None
        self.receive_handler = None
        self.sent_handler = None

        self.local_endpoint = local_endpoint
        self.remote_endpoint = remote_endpoint
        self.transport_properties = transport_properties
        self.number_of_connections = 0
        self.connection_limit = None

        if self.transport_properties is not None:
            json_representation = self.transport_properties.to_json()
            if json_representation is None:
                shim_print("No protocols support given properties")
                exit(1)
            shim_print(json_representation)
            neat_set_property(self.__context, self.__flow, json_representation)

        return

    def initiate(self):
        self.__ops.on_connected = client_on_connected
        self.__ops.on_close = client_on_close
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
        shim_print("LISTEN!")
        listner = Listener(self.__context, self.__flow, self.__ops, self)
        return

    @staticmethod
    def handle_connected(ops):
        precon = Preconnection.preconnection_list[0]
        precon.number_of_connections += 1
        new_connection = Connection(ops, precon)
        # self.ready_handler(new_connection)
        return NEAT_OK
