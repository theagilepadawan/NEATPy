import sys
from enum import Enum, auto
import math, os

from utils import shim_print


class InterfaceTypes(Enum):
    WIFI = auto()
    WIRED = auto()
    CELLULAR = auto()
    LOOPBACK = auto()
    # ???


class AddressPreference(Enum):
    STABLE = auto()
    TEMPORARY = auto()


class SupportedProtocolStacks(Enum):
    UDP = 1
    TCP = 3
    MPTCP = 4
    SCTP = 5

    # SCTP_UDP = "SCTP/UDP"
    # UDP_LITE = "UDP-Lite"

    @staticmethod
    def get_protocol_stack_on_system():
        # Base candidates
        ret = [SupportedProtocolStacks.TCP, SupportedProtocolStacks.UDP]
        if os.path.exists("/usr/include/netinet/sctp.h"):
            ret.append(SupportedProtocolStacks.SCTP)
            shim_print("SCTP supported on system")

    @staticmethod
    def check_for_mptcp():
        if os.path.exists("/proc/sys/net/mptcp/mptcp_enabled"):
            with open('mptcp_enabled') as f:
                status = int(f.readline().strip())
                return status > 0


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


class CapacityProfiles(Enum):
    DEFAULT = auto()
    LOW_LATENCY = auto()


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
