# coding=utf-8

from neat import *
from connection import Connection
from utils import *
import sys
import copy
from time import time
import threading
import multiprocessing
from colorama import Fore, Back, Style

class Preconnection:
    """The TAPS preconnection class.

    Attributes:
        local_endpoint (LocalEndpoint, optional):
                        LocalEndpoint of the
                        preconnection, required if the connection
                        will be used to listen
        remote_endpoint (RemoteEndpoint, optional):
                        RemoteEndpoint of the
                        preconnection, required if a connection
                        will be initiated
        transport_properties (TransportProperties, optional):
                        Object of the transport properties
                        with specified preferenceLevels
    """

    def __init__(self, local_endpoint=None, remote_endpoint=None,
                 transport_properties=None,
                 security_parameters=None):
        self.ctx = neat_init_ctx()
        self.flow = neat_new_flow(self.ctx)
        self.ops = neat_flow_operations()

        neat_log_level(self.ctx, NEAT_LOG_DEBUG)
        neat_set_operations(self.ctx, self.flow, self.ops)
        self.established_connection = None
        self.local_endpoint = local_endpoint
        self.remote_endpoint = remote_endpoint

        if transport_properties is not None:
            json_representation = transport_properties.to_json()
            if json_representation == None:
                exit(1)
            print(json_representation)
            neat_set_property(self.ctx, self.flow, json_representation)

        return

    def initiate(self):
        self.ops.on_connected = client_on_connected
        self.ops.on_close = client_on_close

        neat_set_operations(self.ctx, self.flow, self.ops)

        if (neat_open(self.ctx, self.flow, self.remote_endpoint.address, self.remote_endpoint.port, None, 0)):
            sys.exit("neat_open failed")

        shim_print("CLIENT RUNNING NEAT INITIATED FROM PYTHON")

        neat_start_event_loop(self.ctx, NEAT_RUN_DEFAULT)
        #neat_free_ctx(self.ctx)
        return

    def listen(self):
        shim_print("LISTEN!")
        test = self
        def on_con(ops):
            Connection(test)
            on_connected(ops)

        self.ops.on_connected = on_con #on_connected
        self.ops.on_readable = on_readable

        neat_set_operations(self.ctx, self.flow, self.ops)
        if (neat_accept(self.ctx, self.flow, self.local_endpoint.port, None, 0)):
            sys.exit("neat_accept failed")

        shim_print("A SERVER RUNNING NEAT STARTING FROM PYTHON 🎊")
        neat_start_event_loop(self.ctx, NEAT_RUN_DEFAULT)
        return


############################### SERVER CALLBACKS ###############################
def on_connected(ops):
    shim_print("ON CONNECTED RAN")
    ops.on_writable = on_writable
    ops.on_all_written = on_all_written
    neat_set_operations(ops.ctx, ops.flow, ops)
    buffer = charArr(32)
    bytes_read = new_size_tp()
    size_tp_assign(bytes_read, 32)


    try:
        neat_get_property(ops.ctx, ops.flow, "transport", buffer, bytes_read)
        byte_array = bytearray(size_tp_value(bytes_read))
        for i in range(size_tp_value(bytes_read)):
            byte_array[i] = buffer[i]

        shim_print("Transport protocol used" + Fore.CYAN + " {}".format(byte_array.decode()) + Fore.RESET)
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))


    # Connection(self.ctx, self.flow, ops)
    return NEAT_OK


def on_writable(ops):
    #thread1 = threading.Thread(target=writeable_thread, args=(ops,)).start()
    shim_print("ON WRITABLE RAN")
    message = b"Hello, this is NEAT!"
    neat_write(ops.ctx, ops.flow, message, 20, None, 0)
    ops.on_writable = None
    neat_set_operations(ops.ctx, ops.flow, ops)
    return NEAT_OK


def on_all_written(ops):
    neat_close(ops.ctx, ops.flow)
    return NEAT_OK


def on_readable(ops):
    read(ops)
    return NEAT_OK


############################### SERVER CALLBACKS END ###############################


############################### CLIENT CALLBACKS ###################################
def client_on_readable(ops):
    read(ops)
   # neat_close(ops.ctx, ops.flow)
    return NEAT_OK


def client_on_close(ops):
    shim_print("ON CLOSE RAN")
    neat_stop_event_loop(ops.ctx)
    return NEAT_OK

def client_on_writable(ops):
    #thread1 = multiprocessing.Process(target=writeable_thread_cli, args=(ops,)).start()
    shim_print("ON WRITABLE RAN")
    #message = b"Hi!"
    message = b"GET / HTTP/1.1\r\nHost: weevil.info\r\nUser-agent: libneat\r\nConnection: close\r\n\r\n"

    try:
        #neat_write(ops.ctx, ops.flow, message, 3, None, 0)
        neat_write(ops.ctx, ops.flow, message, len(message), None, 0)
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))

    return NEAT_OK


def client_on_all_written(ops):
    shim_print("ON ALL WRITTEN RAN")
    ops.on_readable = client_on_readable
    ops.on_writable = None
    neat_set_operations(ops.ctx, ops.flow, ops)
    return NEAT_OK


def client_on_connected(ops):
    shim_print("ON CONNECTED RAN")
    ops.on_writable = client_on_writable
    ops.on_all_written = client_on_all_written
    neat_set_operations(ops.ctx, ops.flow, ops)
    return NEAT_OK

############################### CLIENT CALLBACKS END ###############################

############################### COMMON #############################################
new_file = f= open("site.html","w+")
def read(ops):
    shim_print("ON READABLE")
    num = 32*1024*1024
    buffer = charArr(num)
    bytes_read = new_uint32_tp()
    try:
        neat_read(ops.ctx, ops.flow, buffer, num-1, bytes_read, None, 0)
        byte_array = bytearray(uint32_tp_value(bytes_read))
        for i in range(uint32_tp_value(bytes_read)):
            byte_array[i] = buffer[i]

        shim_print("Read {} bytes: {}".format(uint32_tp_value(bytes_read), byte_array.decode()))
        new_file.write(byte_array.decode())
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))


