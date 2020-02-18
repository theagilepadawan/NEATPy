import copy
import sys

import backend
import math;
from neat import *
from connection import *
from utils import *


class Listener():
    listener_list = {}

    def __init__(self, context, flow, ops, preconnection):
        self.__ops = ops
        self.__context = context
        self.__flow = flow

        self.preconnection = preconnection
        self.props = copy.deepcopy(preconnection.transport_properties)
        self.number_of_connections = 0
        self.connection_limit = math.inf

        # Todo: Find a more sophisticated way to keep track of listeners (or is it necessary?)
        Listener.listener_list[0] = self

        self.__ops.on_connected = self.handle_connected
        self.__ops.on_readable = handle_readable

        neat_set_operations(self.__context, self.__flow, self.__ops)

        if neat_accept(self.__context, self.__flow, preconnection.local_endpoint.port, None, 0):
            sys.exit("neat_accept failed")

        shim_print("A SERVER RUNNING NEAT STARTING FROM PYTHON 🎊")
        backend.start(self.__context)
        backend.clean_up(self.__context)

    def stop(self):
        shim_print("LISTENER STOP")
        backend.stop(self.__context)

    def set_new_connection_limit(self, value):
        self.connection_limit = value

    def reset_connection_limit(self):
        self.connection_limit = math.inf

    @staticmethod
    def handle_connected(ops):
        listener = Listener.listener_list[0]
        if listener.connection_limit > listener.number_of_connections:
            listener.number_of_connections += 1

            new_connection = Connection(ops, listener.preconnection, 'passive', listener)
        else:
            shim_print("Connection limit is reached!")

        return NEAT_OK
