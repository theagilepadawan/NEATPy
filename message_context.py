from enum import Enum, auto
import math
from enumerations import *


class MessageContext:
    def __init__(self):
        self.props = {message_property: MessageContextProperties.get_default(message_property) for
                      name, message_property in MessageContextProperties.__members__.items()}


class MessageContextProperties(Enum):
    """
    [From draft-ietf-taps-interface-latest - https://ietf-tapswg.github.io/api-drafts/draft-ietf-taps-interface.html]
    << Applications may need to annotate the Messages they send with extra information to control how data is scheduled
    and processed by the transport protocols in the Connection. Therefore a message context containing these properties
    can be passed to the Send Action. >>
    """
    LIFETIME = 'msg-lifetime'
    PRIORITY = 'msg-prio'
    ORDERED = 'msg-ordered'
    IDEMPOTENT = 'idempotent'
    FINAL = 'final'
    CORRUPTION_PROTECTION_LENGTH = 'msg-checksum-len'
    RELIABLE_DATA_TRANSFER = 'msg-reliable'
    MESSAGE_CAPACITY_PROFILE_OVERRIDE = 'msg-capacity-profile'
    SINGULAR_TRANSMISSION = 'singular-transmission'

    @staticmethod
    def get_default(prop):
        defaults = {
            MessageContextProperties.LIFETIME: math.inf,
            MessageContextProperties.PRIORITY: 100,
            MessageContextProperties.ORDERED: True,
            MessageContextProperties.IDEMPOTENT: False,
            MessageContextProperties.FINAL: False,
            MessageContextProperties.CORRUPTION_PROTECTION_LENGTH: -1,
            MessageContextProperties.RELIABLE_DATA_TRANSFER: True,
            MessageContextProperties.MESSAGE_CAPACITY_PROFILE_OVERRIDE: CapacityProfiles.DEFAULT,
            MessageContextProperties.SINGULAR_TRANSMISSION: False,
        }
        return defaults[prop]
