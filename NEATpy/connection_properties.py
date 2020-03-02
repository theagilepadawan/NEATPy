import sys
from enum import Enum, auto

from enumerations import CapacityProfiles
from utils import shim_print


class ConnectionProperties(Enum):
    RETRANSMISSION_THRESHOLD_BEFORE_EXCESSIVE_RETRANSMISSION_NOTIFICATION = 'retransmit-notify-threshold' #: Default value is -1
    REQUIRED_MINIMUM_CORRUPTION_PROTECTION_COVERAGE_FOR_RECEIVING = 'recv-checksum-len' #: Default value is -1
    PRIORITY = 'conn-prio' #: Default value is 100
    TIMEOUT_FOR_ABORTING_CONNECTION = 'conn-timeout' #: Default value is -1
    CONNECTION_GROUP_TRANSMISSION_SCHEDULER = 'conn-scheduler' #: Default value is "Weighted fair queueing"
    MAXIMUM_MESSAGE_SIZE_CONCURRENT_WITH_CONNECTION_ESTABLISHMENT = 'zero-rtt-msg-max-len' #: Default value is -1
    MAXIMUM_MESSAGE_SIZE_BEFORE_FRAGMENTATION_OR_SEGMENTATION = 'singular-transmission-msg-max-len' #: Default value is -1
    MAXIMUM_MESSAGE_SIZE_ON_SEND = 'send-msg-max-len' #: Default value is -1
    MAXIMUM_MESSAGE_SIZE_ON_RECEIVE = 'recv-msg-max-len' #: Default value is -1
    CAPACITY_PROFILE = 'conn-capacity-profile' #: Default value is CapacityProfiles.DEFAULT
    BOUNDS_ON_SEND_OR_RECEIVE_RATE = 'max-send-rate / max-recv-rate' #: Default value is (-1, -1)
    USER_TIMEOUT_TCP = 'tcp-uto'  #: Add three members here?

    def __str__(self):
        return self.value

    @staticmethod
    def get_default(prop=None):
        defaults = {
            ConnectionProperties.RETRANSMISSION_THRESHOLD_BEFORE_EXCESSIVE_RETRANSMISSION_NOTIFICATION: -1,
            ConnectionProperties.REQUIRED_MINIMUM_CORRUPTION_PROTECTION_COVERAGE_FOR_RECEIVING: -1,
            ConnectionProperties.PRIORITY: 100,
            ConnectionProperties.TIMEOUT_FOR_ABORTING_CONNECTION: -1,
            ConnectionProperties.CONNECTION_GROUP_TRANSMISSION_SCHEDULER: "Weighted fair queueing",
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_CONCURRENT_WITH_CONNECTION_ESTABLISHMENT: -1, # TODO: Make sure this is set during connection creation
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_BEFORE_FRAGMENTATION_OR_SEGMENTATION: -1, # TODO: Make sure this is set during connection creation
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND: -1,
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE: -1,
            ConnectionProperties.CAPACITY_PROFILE: CapacityProfiles.DEFAULT,
            ConnectionProperties.BOUNDS_ON_SEND_OR_RECEIVE_RATE: (-1, -1),
            ConnectionProperties.USER_TIMEOUT_TCP: {TCPUserTimeout.ADVERTISED_USER_TIMEOUT: 300,  # TCP default
                                                    TCPUserTimeout.USER_TIMEOUT_ENABLED: False,
                                                    TCPUserTimeout.CHANGEABLE: True}
        }

        if prop:
            return defaults[prop]
        else:
            # TCP UTO should only be added if TCP becomes the chosen transport protocol
            return defaults

    @staticmethod
    def is_read_only(connection_property):
        read_only_props = [
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND,
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE,
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_BEFORE_FRAGMENTATION_OR_SEGMENTATION,
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_CONCURRENT_WITH_CONNECTION_ESTABLISHMENT
        ]
        return connection_property in read_only_props

    @staticmethod
    def set_property(connection_props, prop_to_set, value):
        if not ConnectionProperties.is_valid_property(prop_to_set):
            shim_print("Given property not valid - Ignoring...", level='error')
        elif ConnectionProperties.is_read_only(prop_to_set):
            shim_print("Given property is read only - Ignoring...", level='error')
        else:
            if prop_to_set is ConnectionProperties.USER_TIMEOUT_TCP:
                ConnectionProperties.set_tcp_uto(connection_props, value)
            else:
                connection_props[prop_to_set] = value

    @staticmethod
    def set_tcp_uto(connection_props, values):
        prev_timeout_val = connection_props[ConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.ADVERTISED_USER_TIMEOUT]
        prev_enabled_bool = connection_props[ConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.USER_TIMEOUT_ENABLED]

        if sys.platform != 'linux':
            shim_print("TCP UTO is only available on Linux", level='error')
            return
        for tcp_uto_parameter, tcp_uto_value in values.items():
            if tcp_uto_parameter is TCPUserTimeout.ADVERTISED_USER_TIMEOUT:
                connection_props[ConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.ADVERTISED_USER_TIMEOUT] = tcp_uto_value
            elif tcp_uto_parameter is TCPUserTimeout.USER_TIMEOUT_ENABLED:
                connection_props[ConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.USER_TIMEOUT_ENABLED] = tcp_uto_value
            elif tcp_uto_parameter is TCPUserTimeout.CHANGEABLE:
                connection_props[ConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.CHANGEABLE] = tcp_uto_value
            else:
                shim_print("No valid TCP UTO parameter", level='error')

    @staticmethod
    def is_valid_property(given_property):
        return isinstance(given_property, ConnectionProperties)


class TCPUserTimeout(Enum):
    ADVERTISED_USER_TIMEOUT = 'tcp.user-timeout-value'
    USER_TIMEOUT_ENABLED = 'tcp.user-timeout'
    CHANGEABLE = 'tcp.user-timeout-recv'
