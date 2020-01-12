from neat import *
from utils import *
import sys
from colorama import Fore, Back, Style


############################### SERVER CALLBACKS ###############################
# def on_connected(ops):
#     shim_print("ON CONNECTED RAN")
#     #ops.on_writable = on_writable
#     ops.on_all_written = on_all_written
#     neat_set_operations(ops.ctx, ops.flow, ops)
#     buffer = charArr(32)
#     bytes_read = new_size_tp()
#     size_tp_assign(bytes_read, 32)
#
#     try:
#         neat_get_property(ops.ctx, ops.flow, "transport", buffer, bytes_read)
#         byte_array = bytearray(size_tp_value(bytes_read))
#         for i in range(size_tp_value(bytes_read)):
#             byte_array[i] = buffer[i]
#
#         shim_print("Transport protocol used" + Fore.CYAN + " {}".format(byte_array.decode()) + Fore.RESET)
#     except:
#         shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))
#
#     # Connection(self.ctx, self.flow, ops)
#     return NEAT_OK
#
#
# def on_writable(ops):
#     shim_print("ON WRITABLE RAN")
#     message = b"Hello, this is NEAT!"
#     neat_write(ops.ctx, ops.flow, message, 20, None, 0)
#     ops.on_writable = None
#     neat_set_operations(ops.ctx, ops.flow, ops)
#     return NEAT_OK
#
#
def on_all_written(ops):
    neat_close(ops.ctx, ops.flow)
    return NEAT_OK





############################### SERVER CALLBACKS END ###############################


############################### CLIENT CALLBACKS ###################################
def client_on_readable(ops):
    read(ops)
    neat_close(ops.ctx, ops.flow)
    return NEAT_OK


def client_on_close(ops):
    shim_print("ON CLOSE RAN")
    neat_stop_event_loop(ops.ctx)
    return NEAT_OK


def client_on_writable(ops):
    shim_print("ON WRITABLE RAN")
    message = b"Hi!"

    try:
        neat_write(ops.ctx, ops.flow, message, 3, None, 0)
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))
    return NEAT_OK


def client_on_all_written(ops):
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


def read(ops):
    shim_print("ON READABLE")
    shim_print(ops.flow)
    buffer = charArr(32)
    bytes_read = new_uint32_tp()
    try:
        neat_read(ops.ctx, ops.flow, buffer, 31, bytes_read, None, 0)
        byte_array = bytearray(uint32_tp_value(bytes_read))
        for i in range(uint32_tp_value(bytes_read)):
            byte_array[i] = buffer[i]

        shim_print("Read {} bytes: {}".format(uint32_tp_value(bytes_read), byte_array.decode()))
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))
