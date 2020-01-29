from neat import *
from neat import charArr, new_uint32_tp, neat_read, uint32_tp_value
from utils import *
import sys
from enum import Enum, auto

from utils import shim_print

DEBUG = 0


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
        return byte_array.decode()
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))


def stop_neat(context):
    neat_stop_event_loop(context)


def abort_neat(context, flow):
    neat_abort(context, flow)


def get_flow_fd(flow):
    return neat_get_socket_fd(flow)


def read(ops):
    shim_print("ON READABLE")
    buffer = charArr(32)
    bytes_read = new_uint32_tp()
    try:
        neat_read(ops.ctx, ops.flow, buffer, 31, bytes_read, None, 0)
        byte_array = bytearray(uint32_tp_value(bytes_read))
        for i in range(uint32_tp_value(bytes_read)):
            byte_array[i] = buffer[i]

        shim_print("Read {} bytes: {}".format(uint32_tp_value(bytes_read), byte_array.decode()), level="msg")
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))


def write(ops, message):
    try:
        neat_write(ops.ctx, ops.flow, message, len(message), None, 0)
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]))
        return 1
    return 0


def set_neat_callbacks(ops, *callbacks):
    for tup in callbacks:
        pass



class NeatCallbacks(Enum):
    ON_CONNECTED = lambda ops, value : NeatCallbacks.set_ops(ops.on_connected, value)
    ON_ERROR = lambda ops, value : NeatCallbacks.set_ops(ops.on_error, value)
    ON_READABLE = lambda ops, value : NeatCallbacks.set_ops(ops.on_readable, value)
    ON_WRITABLE = lambda ops, value : NeatCallbacks.set_ops(ops.on_writable, value)
    ON_ALL_WRITTEN = lambda ops, value : NeatCallbacks.set_ops(ops.on_all_written, value)
    ON_NETWORK_STATUS_CHANGED = lambda ops, value : NeatCallbacks.set_ops(ops.on_network_status_changed, value)
    ON_ABORTED = lambda ops, value : NeatCallbacks.set_ops(ops.on_aborted, value)
    ON_TIMEOUT = lambda ops, value : NeatCallbacks.set_ops(ops.on_timeout, value)
    ON_CLOSE = lambda ops, value : NeatCallbacks.set_ops(ops.on_close, value)
    ON_SEND_FAILURE = lambda ops, value : NeatCallbacks.set_ops(ops.on_send_failure, value)
    ON_SLOWDOWN = auto()  # Not implemented in NEAT
    ON_RATE_INIT = auto()  # Not implemented in NEAT

    @staticmethod
    def set_ops(member, value):
        member = value
