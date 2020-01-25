from enum import Enum, auto
from enumerations import *


class SelectionProperties(Enum):
    RELIABILITY = 'reliability'
    PRESERVE_MSG_BOUNDARIES = 'preserve-msg-boundaries'
    PER_MSG_RELIABILITY = 'per-msg-reliability'
    PRESERVE_ORDER = 'preserve-order'
    ZERO_RTT_MSG = 'zero-rtt-msg'
    MULTISTREAMING = 'multistreaming'
    PER_MSG_CHECKSUM_LEN_SEND = 'per-msg-checksum-len-send'
    PER_MSG_CHECKSUM_LEN_RECV = 'per-msg-checksum-len-recv'
    CONGESTION_CONTROL = 'congestion-control'
    INTERFACE = 'interface'
    MULTIPATH = 'multipath'
    DIRECTION = CommunicationDirections.BIDIRECTIONAL
    RETRANSMIT_NOTIFY = 'retransmit-notify'
    SOFT_ERROR_NOTIFY = 'soft-error-notify'

    def __str__(self):
        return self.value

    @staticmethod
    def get_default(prop=None):
        defaults = {
            SelectionProperties.RELIABILITY: PreferenceLevel.REQUIRE,
            SelectionProperties.PRESERVE_MSG_BOUNDARIES: PreferenceLevel.PREFER,
            SelectionProperties.PER_MSG_RELIABILITY: PreferenceLevel.IGNORE,
            SelectionProperties.PRESERVE_ORDER: PreferenceLevel.REQUIRE,
            SelectionProperties.ZERO_RTT_MSG: PreferenceLevel.IGNORE,
            SelectionProperties.MULTISTREAMING: PreferenceLevel.PREFER,
            SelectionProperties.PER_MSG_CHECKSUM_LEN_SEND: PreferenceLevel.IGNORE,
            SelectionProperties.PER_MSG_CHECKSUM_LEN_RECV: PreferenceLevel.IGNORE,
            SelectionProperties.CONGESTION_CONTROL: PreferenceLevel.REQUIRE,
            SelectionProperties.INTERFACE: (), # TODO: Settle on a reasoable default
            SelectionProperties.MULTIPATH: PreferenceLevel.PREFER,
            SelectionProperties.DIRECTION: CommunicationDirections.BIDIRECTIONAL,
            SelectionProperties.RETRANSMIT_NOTIFY: PreferenceLevel.IGNORE,
            SelectionProperties.SOFT_ERROR_NOTIFY: PreferenceLevel.IGNORE
        }
        if prop:
            return defaults[prop]
        else:
            return defaults
