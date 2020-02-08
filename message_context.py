from enum import Enum, auto
import math
from enumerations import *
from message_properties import *
from framer import *


class MessageContext:
    def __init__(self):
        self.props = {message_property: MessageProperties.get_default(message_property) for
                      name, message_property in MessageProperties.__members__.items()}
        self.framer_values = {}

    def add(self, framer: Framer, key, value):
        if not isinstance(framer, Framer):
            shim_print("Provided argument is not a valid framer - ignoring", level='error')
        self.framer_values[key] = (framer, value)

    def get(self, framer, key):
        value_dict = self.framer_values
        if key in value_dict and isinstance(framer, type(value_dict[key][0])):
            return value_dict[key]
        else:
            return None

