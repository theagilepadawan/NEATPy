from neat import *
from utils import *
import sys


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
