import sys
from enum import Enum, auto
import math, os

from selection_properties import SelectionProperties
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


class AdditionalServices(Enum):
    PROTECTION_AGAINST_DUPLICATED_MESSAGES = auto()


class SupportedProtocolStacks(Enum):
    UDP = 1
    TCP = 3
    MPTCP = 4
    SCTP = 5
    # SCTP_UDP = "SCTP/UDP"
    # UDP_LITE = "UDP-Lite"

    @staticmethod
    def get_service_level(stack, service):
        protocols_services = {
            SupportedProtocolStacks.TCP: {
                SelectionProperties.RELIABILITY: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.PRESERVE_MSG_BOUNDARIES: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PER_MSG_RELIABILITY: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PRESERVE_ORDER: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.ZERO_RTT_MSG: ServiceLevel.OPTIONAL,
                SelectionProperties.MULTISTREAMING: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PER_MSG_CHECKSUM_LEN_SEND: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PER_MSG_CHECKSUM_LEN_RECV: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.CONGESTION_CONTROL: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.MULTIPATH: ServiceLevel.OPTIONAL,
                # should be not provided and add MTPCP as standalone stack?
                SelectionProperties.DIRECTION: ServiceLevel.INTRINSIC_SERVICE,  # add proper defaults
                SelectionProperties.RETRANSMIT_NOTIFY: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.SOFT_ERROR_NOTIFY: ServiceLevel.INTRINSIC_SERVICE,
                AdditionalServices.PROTECTION_AGAINST_DUPLICATED_MESSAGES: ServiceLevel.INTRINSIC_SERVICE
            },

            SupportedProtocolStacks.SCTP: {
                SelectionProperties.RELIABILITY: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.PRESERVE_MSG_BOUNDARIES: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.PER_MSG_RELIABILITY: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.PRESERVE_ORDER: ServiceLevel.OPTIONAL,
                SelectionProperties.ZERO_RTT_MSG: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.MULTISTREAMING: ServiceLevel.OPTIONAL,
                SelectionProperties.PER_MSG_CHECKSUM_LEN_SEND: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PER_MSG_CHECKSUM_LEN_RECV: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.CONGESTION_CONTROL: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.MULTIPATH: ServiceLevel.OPTIONAL,
                SelectionProperties.DIRECTION: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.RETRANSMIT_NOTIFY: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.SOFT_ERROR_NOTIFY: ServiceLevel.OPTIONAL,
                AdditionalServices.PROTECTION_AGAINST_DUPLICATED_MESSAGES: ServiceLevel.INTRINSIC_SERVICE
            },

            SupportedProtocolStacks.UDP: {
                SelectionProperties.RELIABILITY: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PRESERVE_MSG_BOUNDARIES: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.PER_MSG_RELIABILITY: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PRESERVE_ORDER: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.ZERO_RTT_MSG: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.MULTISTREAMING: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PER_MSG_CHECKSUM_LEN_SEND: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.PER_MSG_CHECKSUM_LEN_RECV: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.CONGESTION_CONTROL: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.MULTIPATH: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.DIRECTION: ServiceLevel.INTRINSIC_SERVICE,
                SelectionProperties.RETRANSMIT_NOTIFY: ServiceLevel.NOT_PROVIDED,
                SelectionProperties.SOFT_ERROR_NOTIFY: ServiceLevel.INTRINSIC_SERVICE,
                AdditionalServices.PROTECTION_AGAINST_DUPLICATED_MESSAGES: ServiceLevel.NOT_PROVIDED
            }
        }
        return protocols_services[stack][service].value

    @staticmethod
    def get_protocol_stacks_on_system():
        # Base candidates
        ret = [SupportedProtocolStacks.TCP, SupportedProtocolStacks.UDP]
        if os.path.exists("/usr/include/netinet/sctp.h"):
            ret.append(SupportedProtocolStacks.SCTP)
            shim_print("SCTP supported on system")
        return ret

    @staticmethod
    def check_for_mptcp():
        if os.path.exists("/proc/sys/net/mptcp/mptcp_enabled"):
            with open("/proc/sys/net/mptcp/mptcp_enabled") as f:
                status = int(f.readline().strip())
                return status > 0


class ServiceLevel(Enum):
    INTRINSIC_SERVICE = 2
    OPTIONAL = 0
    NOT_PROVIDED = -2


class PreferenceLevel(Enum):
    """
    An enumeration.
    Used when specifying a preference for :py:class:`selection_properties`.

    E.g an application specifying that a reliable transport is required would do this the following way::
        tp.add(SelectionProperties.RELIABILITY, PreferenceLevel.REQUIRE)
    """
    REQUIRE = 2
    PREFER = 1
    IGNORE = 0
    AVOID = -1
    PROHIBIT = -2


class CapacityProfiles(Enum):
    DEFAULT = auto()
    LOW_LATENCY = auto()


class ConnectionEvents(Enum):
    EXPIRED = auto()
    CLOSED = auto()

    INITIATE_ERROR = 'Initiate error'
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
    READY = auto()


class ListenerEvents(Enum):
    CONNECTION_RECEIVED = auto()
    STOPPED = auto()
    LISTEN_ERROR = auto()


class Events(Enum):
    _ConnectionEvents = ConnectionEvents
    _PreconnectionEvents = PreconnectionEvents
    _ListenerEvents = ListenerEvents
