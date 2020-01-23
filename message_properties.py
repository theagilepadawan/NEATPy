from enum import Enum, auto
import math
from enumerations import *


class MessageProperties(Enum):
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

    def __str__(self):
        return self.value

    @staticmethod
    def get_default(prop=None):
        defaults = {
            MessageProperties.LIFETIME: math.inf,
            MessageProperties.PRIORITY: 100,
            MessageProperties.ORDERED: True,
            MessageProperties.IDEMPOTENT: False,
            MessageProperties.FINAL: False,
            MessageProperties.CORRUPTION_PROTECTION_LENGTH: -1,
            MessageProperties.RELIABLE_DATA_TRANSFER: True,
            MessageProperties.MESSAGE_CAPACITY_PROFILE_OVERRIDE: CapacityProfiles.DEFAULT,
            MessageProperties.SINGULAR_TRANSMISSION: False,
        }

        if prop:
            return defaults[prop]
        else:
            return defaults
