from neat import *
from neat import charArr, new_uint32_tp, neat_read, uint32_tp_value
from utils import *
import sys

from utils import shim_print


def neat_bootstrap():
    ctx = neat_init_ctx()
    flow = neat_new_flow(ctx)
    ops = neat_flow_operations()
    neat_log_level(ctx, NEAT_LOG_DEBUG)
    neat_set_operations(ctx, flow, ops)

    return ctx, flow, ops


def get_transport_stack_used(ctx, flow):
    buffer = charArr(32)
    bytes_read = new_size_tp()
    size_tp_assign(bytes_read, 32)

    try:
        neat_get_property(ctx, flow, "transport", buffer, bytes_read)
        byte_array = bytearray(size_tp_value(bytes_read))
        for i in range(size_tp_value(bytes_read)):
            byte_array[i] = buffer[i]

        # shim_print("Transport protocol used" + Fore.CYAN + " {}".format(byte_array.decode()) + Fore.RESET)
        return byte_array.decode()
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))


def stop_neat(context, flow):
    neat_abort(context, flow)


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


