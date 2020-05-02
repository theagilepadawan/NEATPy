from enum import Enum, auto
import math

from connection_properties import CapacityProfiles
from utils import shim_print


class MessageProperties(Enum):
    """ [From draft-ietf-taps-interface-latest - https://ietf-tapswg.github.io/api-drafts/draft-ietf-taps-interface.html]
    << Applications may need to annotate the Messages they send with extra information to control how data is scheduled
    and processed by the transport protocols in the Connection. Therefore a message context containing these properties
    can be passed to the Send Action. >>
    """
    LIFETIME = 'msg-lifetime' #: Default value is math.inf
    PRIORITY = 'msg-prio' #: Default value is 100
    ORDERED = 'msg-ordered' #: Default value is True
    IDEMPOTENT = 'idempotent' #: Default value is False
    FINAL = 'final' #: Default value is False
    CORRUPTION_PROTECTION_LENGTH = 'msg-checksum-len' #: Default value is -1
    RELIABLE_DATA_TRANSFER = 'msg-reliable' #: Default value is True
    MESSAGE_CAPACITY_PROFILE_OVERRIDE = 'msg-capacity-profile' #: Default value is CapacityProfiles.DEFAULT
    SINGULAR_TRANSMISSION = 'singular-transmission' #: Default value is False

    # Ready-only, receive message properties:
    ECN = 'ecn' #: Read only property
    EARLY_DATA = 'early-data' #: Read only property
    RECEIVING_FINAL_MESSAGE = 'receiving-final-messages' #: Read only property

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
            MessageProperties.ECN: None,
            MessageProperties.EARLY_DATA: None,
            MessageProperties.RECEIVING_FINAL_MESSAGE: None
        }

        if prop:
            return defaults[prop]
        else:
            return defaults

    @staticmethod
    def set_property(given_props, prop, value):
        if not isinstance(value, type(MessageProperties.get_default(prop))):
            shim_print(
                f"Incompatible value type provided - Needed {type(MessageProperties.get_default(prop))}, got {type(value)}", level='error')
        else:
            given_props[prop] = value
