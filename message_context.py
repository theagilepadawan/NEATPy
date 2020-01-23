from enum import Enum, auto
import math
from enumerations import *
from message_properties import *


class MessageContext:
    def __init__(self):
        self.props = {message_property: MessageProperties.get_default(message_property) for
                      name, message_property in MessageProperties.__members__.items()}
