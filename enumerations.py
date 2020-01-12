from enum import Enum, auto
import math


class SupportedProtocolStacks(Enum):
    SCTP = "SCTP"
    SCTP_UDP = "SCTP/UDP"
    TCP = "TCP"
    UDP = "UDP"
    UDP_LITE = "UDP-Lite"
    MPTCP = "MPTCP"


class ServiceLevel(Enum):
    INTRINSIC_SERVICE = 2
    OPTIONAL = 0
    NOT_PROVIDED = -2


class PreferenceLevel(Enum):
    REQUIRE = 2
    PREFER = 1
    IGNORE = 0
    AVOID = -1
    PROHIBIT = -2


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
    MULTIPATH = 'multipath'
    # DIRECTION = 'direction'
    RETRANSMIT_NOTIFY = 'retransmit-notify'
    SOFT_ERROR_NOTIFY = 'soft-error-notify'

    def __str__(self):
        return self.value

    @staticmethod
    def get_default(prop):
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
            SelectionProperties.MULTIPATH: PreferenceLevel.PREFER,
            # SelectionPropertiesDefaults.DIRECTION: CommunicationDirections.BIDIRECTIONAL,
            SelectionProperties.RETRANSMIT_NOTIFY: PreferenceLevel.REQUIRE,
            SelectionProperties.SOFT_ERROR_NOTIFY: PreferenceLevel.REQUIRE
        }

        return defaults[prop]


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

    @staticmethod
    def get_default(prop):
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
        return defaults[prop]


class CapacityProfiles(Enum):
    DEFAULT = auto()
    LOW_LATENCY = auto()


class CommunicationDirections(Enum):
    """
    [From draft-ietf-taps-interface-latest - https://ietf-tapswg.github.io/api-drafts/draft-ietf-taps-interface.html]
    << This property specifies whether an application wants to use the connection for sending and/or receiving data.
    Possible values are: Bidirectional: The connection must support sending and receiving data

    Unidirectional send:
    The connection must support sending data, and the application cannot use the connection to receive any data

    Unidirectional receive: The connection must support receiving data, and the application cannot use the connection
    to send any data The default is bidirectional. Since unidirectional communication can be supported by transports
    offering bidirectional communication, specifying unidirectional communication may cause a transport stack that
    supports bidirectional communication to be selected. >>
    """
    BIDIRECTIONAL = auto()
    UNIDIRECTIONAL_SEND = auto()
    UNIDIRECTIONAL_RECEIVE = auto()
