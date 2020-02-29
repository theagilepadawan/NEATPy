from enum import Enum, auto
import math
from enumerations import *
from message_properties import *
from framer import Framer


class MessageContext:
    def __init__(self):
        self.props = {message_property: MessageProperties.get_default(message_property) for
                      name, message_property in MessageProperties.__members__.items()}
        self.framer_values = {}

        # Information possible for applications to query at send and receive events
        self.remote_endpoint = None
        self.local_endpoint = None

    def reply(self):
        return NotImplementedError

    def get_original_request(self):
        return NotImplementedError

    def get_remote_endpoint(self):
        return self.remote_endpoint

    def get_local_endpoint(self):
        return self.local_endpoint

    def add(self, key, value, scope: Framer = None):
        # If scope is not set, try to add message property
        if not scope:
            if not isinstance(key, MessageProperties):
                shim_print("Invalid message property provided - ignoring", level='error')
            else:
                self.props[key] = value
        # Else a framer is given, try to add meta-data
        else:
            framer = scope
            if not isinstance(framer, Framer):
                shim_print("Provided argument is not a valid framer - ignoring", level='error')
                self.framer_values[key] = (framer, value)

    def get(self, key, scope=None):
        # If scope is not set, try to get properties
        if not scope:
            if not isinstance(key, MessageProperties):
                shim_print("Invalid message property provided - ignoring", level='error')
            if key not in self.props:
                shim_print("Given message property is not present")
            else:
                return self.props[key]
        # Else a framer is given, try to fetch meta-data
        else:
            framer = scope
            value_dict = self.framer_values
            if key in value_dict and isinstance(framer, type(value_dict[key][0])):
                return value_dict[key]
            else:
                return None
