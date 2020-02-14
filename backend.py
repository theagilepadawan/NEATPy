import json
from neat import *
from neat import charArr, new_uint32_tp, neat_read, uint32_tp_value
import sys
from enum import Enum, auto
from utils import shim_print

DEBUG = 0


def bootstrap_backend():
    ctx = neat_init_ctx()
    flow = neat_new_flow(ctx)
    ops = neat_flow_operations()
    neat_log_level(ctx, NEAT_LOG_DEBUG)
    neat_set_operations(ctx, flow, ops)

    return ctx, flow, ops


class BackendProperties(Enum):
    DOMAIN_NAME = 'domain_name'
    INTERFACE = 'interface'
    PORT = 'port'
    REMOTE_IP = 'remote_ip'
    LOCAL_IP = 'local_ip'
    ADDRESS = 'address'

    # Not in used at the moment, but could be generalized to get a given property with neat_get_property


def get_backend_prop(ctx, flow, back_end_prop: BackendProperties):
    buffer = charArr(1000)
    bytes_read = new_size_tp()
    size_tp_assign(bytes_read, 1000)

    try:
        # neat_get_stack(flow, buffer, bytes_read)
        ret = neat_get_property(ctx, flow, back_end_prop.value, buffer, bytes_read)
        if ret is NEAT_ERROR_UNABLE:
            return None
        byte_array = bytearray(size_tp_value(bytes_read))
        for i in range(size_tp_value(bytes_read)):
            byte_array[i] = buffer[i]
        return byte_array.decode()
    except UnicodeDecodeError:
        shim_print(f"PORT: {int.from_bytes(byte_array, byteorder='little', signed=False)}")
        return int.from_bytes(byte_array, byteorder='little', signed=False)
    except:
        shim_print("An error occurred in the Python callback: {}".format(sys.exc_info()[0]), level='error')


def start(context):
    neat_start_event_loop(context, NEAT_RUN_DEFAULT)


def stop(context):
    neat_stop_event_loop(context)


def clean_up(context):
    neat_free_ctx(context)


# def clone(ctx, endpoint, port, clone_connected_handler):
#     flow = neat_new_flow(ctx)
#     ops = neat_flow_operations()
#
#     def on_clone_error(op):
#         shim_print("Clone opertion at back end", level="error")
#         return NEAT_OK
#
#     ops.on_error = on_clone_error
#     ops.on_writable = clone_connected_handler
#     neat_set_operations(ctx, flow, ops)
#
#     neat_open(ctx, flow, endpoint, port, None, 0)


def initiate(context, flow, address, port, stream_count=None):
    options = None
    opt_count = 0
    if stream_count:
        options = neat_tlv()
        opt_count = 1
        options.tag = NEAT_TAG_STREAM_COUNT
        options.type = NEAT_TYPE_INTEGER
        options.value.integer = 100

    return neat_open(context, flow, address, port, options, opt_count)


def abort(context, flow):
    neat_abort(context, flow)


def read(ops, size):
    shim_print("ON READABLE")
    buffer = charArr(size)
    bytes_read = new_uint32_tp()
    try:
        neat_read(ops.ctx, ops.flow, buffer, size - 1, bytes_read, None, 0)
        byte_array = bytearray(uint32_tp_value(bytes_read))
        for i in range(uint32_tp_value(bytes_read)):
            byte_array[i] = buffer[i]
        message = byte_array.decode()
        return message
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
    ON_CONNECTED = lambda ops, value: NeatCallbacks.set_ops(ops.on_connected, value)
    ON_ERROR = lambda ops, value: NeatCallbacks.set_ops(ops.on_error, value)
    ON_READABLE = lambda ops, value: NeatCallbacks.set_ops(ops.on_readable, value)
    ON_WRITABLE = lambda ops, value: NeatCallbacks.set_ops(ops.on_writable, value)
    ON_ALL_WRITTEN = lambda ops, value: NeatCallbacks.set_ops(ops.on_all_written, value)
    ON_NETWORK_STATUS_CHANGED = lambda ops, value: NeatCallbacks.set_ops(ops.on_network_status_changed, value)
    ON_ABORTED = lambda ops, value: NeatCallbacks.set_ops(ops.on_aborted, value)
    ON_TIMEOUT = lambda ops, value: NeatCallbacks.set_ops(ops.on_timeout, value)
    ON_CLOSE = lambda ops, value: NeatCallbacks.set_ops(ops.on_close, value)
    ON_SEND_FAILURE = lambda ops, value: NeatCallbacks.set_ops(ops.on_send_failure, value)
    ON_SLOWDOWN = auto()  # Not implemented in NEAT
    ON_RATE_INIT = auto()  # Not implemented in NEAT

    @staticmethod
    def set_ops(member, value):
        member = value


def pass_candidates_to_back_end(candidates, context, flow):
    if len(candidates) is 1:
        candiates_to_backend = json.dumps({"transport": {"value": candidates.pop(0).name, "precedence": 1}})
    else:
        candiates_to_backend = json.dumps(
            {"transport": {"value": [candidate.name for candidate in candidates], "precedence": 2}})
    shim_print(candiates_to_backend)
    neat_set_property(context, flow, candiates_to_backend)


def set_timeout(context, flow, new_timeout):
    if neat_change_timeout(context, flow, new_timeout):
        shim_print("Changing timeout failed at back-end", level='error')
    shim_print(f"Timeout changed to {new_timeout} seconds")
