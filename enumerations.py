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
            SelectionProperties.RETRANSMIT_NOTIFY: PreferenceLevel.IGNORE,
            SelectionProperties.SOFT_ERROR_NOTIFY: PreferenceLevel.IGNORE
        }

        return defaults[prop]


class ConnectionProperties(Enum):
    RETRANSMISSION_THRESHOLD_BEFORE_EXCESSIVE_RETRANSMISSION_NOTIFICATION = 'retransmit-notify-threshold'
    REQUIRED_MINIMUM_CORRUPTION_PROTECTION_COVERAGE_FOR_RECEIVING = 'recv-checksum-len'
    PRIORITY = 'conn-prio'
    TIMEOUT_FOR_ABORTING_CONNECTION = 'conn-timeout'
    CONNECTION_GROUP_TRANSMISSION_SCHEDULER = 'conn-scheduler'
    MAXIMUM_MESSAGE_SIZE_CONCURRENT_WITH_CONNECTION_ESTABLISHMENT = 'zero-rtt-msg-max-len'
    MAXIMUM_MESSAGE_SIZE_BEFORE_FRAGMENTATION_OR_SEGMENTATION = 'singular-transmission-msg-max-len'
    MAXIMUM_MESSAGE_SIZE_ON_SEND = 'send-msg-max-len'
    MAXIMUM_MESSAGE_SIZE_ON_RECEIVE = 'recv-msg-max-len'
    CAPACITY_PROFILE = 'conn-capacity-profile'
    BOUNDS_ON_SEND_OR_RECEIVE_RATE = 'max-send-rate / max-recv-rate'
    USER_TIMEOUT_TCP = auto()  # Add three members here?


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


class ConnectionEvents(Enum):
    READY = auto()
    CONNECTION_RECEIVED = auto()
    RENDEZVOUS_DONE = auto()
    EXPIRED = auto()
    CLOSED = auto()

    INITIATE_ERROR = auto()
    CONNECTION_ERROR = auto()
    SOFT_ERROR = auto()
    SEND_ERROR = auto()
    RECEIVE_ERROR = auto()
    CLONED_ERROR = auto()

    EXCESSIVE_RETRANSMISSION = auto()
    RECEIVED = auto()
    RECEIVED_PARTIAL = auto()
    SENT = auto()


class PreconnectionEvents(Enum):
    RENDEZVOUS_DONE = auto()
    RENDEZVOUS_ERROR = auto()


class ListenerEvents(Enum):
    STOPPED = auto()
    LISTEN_ERROR = auto()


class Events(Enum):
    _ConnectionEvents = ConnectionEvents
    _PreconnectionEvents = PreconnectionEvents
    _ListenerEvents = ListenerEvents
