import sys
from enum import Enum, auto

from enumerations import CapacityProfiles
from utils import shim_print


class GenericConnectionProperties(Enum):
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
    USER_TIMEOUT_TCP = 'tcp-uto'  # Add three members here?



    def __str__(self):
        return self.value

    @staticmethod
    def get_default(prop=None):
        defaults = {
            GenericConnectionProperties.RETRANSMISSION_THRESHOLD_BEFORE_EXCESSIVE_RETRANSMISSION_NOTIFICATION: -1,
            GenericConnectionProperties.REQUIRED_MINIMUM_CORRUPTION_PROTECTION_COVERAGE_FOR_RECEIVING: -1,
            GenericConnectionProperties.PRIORITY: 100,
            GenericConnectionProperties.TIMEOUT_FOR_ABORTING_CONNECTION: -1,
            GenericConnectionProperties.CONNECTION_GROUP_TRANSMISSION_SCHEDULER: "Weighted fair queueing",
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_CONCURRENT_WITH_CONNECTION_ESTABLISHMENT: -1, # TODO: Make sure this is set during connection creation
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_BEFORE_FRAGMENTATION_OR_SEGMENTATION: -1, # TODO: Make sure this is set during connection creation
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND: -1,
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE: -1,
            GenericConnectionProperties.CAPACITY_PROFILE: CapacityProfiles.DEFAULT,
            GenericConnectionProperties.BOUNDS_ON_SEND_OR_RECEIVE_RATE: (-1, -1),
            GenericConnectionProperties.USER_TIMEOUT_TCP: {TCPUserTimeout.ADVERTISED_USER_TIMEOUT: 300, # TCP default
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
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND,
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE,
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_BEFORE_FRAGMENTATION_OR_SEGMENTATION,
            GenericConnectionProperties.MAXIMUM_MESSAGE_SIZE_CONCURRENT_WITH_CONNECTION_ESTABLISHMENT
        ]
        return connection_property in read_only_props

    @staticmethod
    def set_property(connection_props, prop_to_set, value):
        if not GenericConnectionProperties.is_valid_property(prop_to_set):
            shim_print("Given property not valid - Ignoring...", level='error')
        elif GenericConnectionProperties.is_read_only(prop_to_set):
            shim_print("Given property is read only - Ignoring...", level='error')
        else:
            if prop_to_set is GenericConnectionProperties.USER_TIMEOUT_TCP:
                GenericConnectionProperties.set_tcp_uto(connection_props, value)
            else:
                connection_props[prop_to_set] = value

    @staticmethod
    def set_tcp_uto(connection_props, values):
        prev_timeout_val = connection_props[GenericConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.ADVERTISED_USER_TIMEOUT]
        prev_enabled_bool = connection_props[GenericConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.USER_TIMEOUT_ENABLED]

        if sys.platform != 'linux':
            shim_print("TCP UTO is only available on Linux", level='error')
            return
        for tcp_uto_parameter, tcp_uto_value in values.items():
            if tcp_uto_parameter is TCPUserTimeout.ADVERTISED_USER_TIMEOUT:
                connection_props[GenericConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.ADVERTISED_USER_TIMEOUT] = tcp_uto_value
            elif tcp_uto_parameter is TCPUserTimeout.USER_TIMEOUT_ENABLED:
                connection_props[GenericConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.USER_TIMEOUT_ENABLED] = tcp_uto_value
            elif tcp_uto_parameter is TCPUserTimeout.CHANGEABLE:
                connection_props[GenericConnectionProperties.USER_TIMEOUT_TCP][TCPUserTimeout.CHANGEABLE] = tcp_uto_value
            else:
                shim_print("No valid TCP UTO parameter", level='error')

    @staticmethod
    def is_valid_property(given_property):
        return isinstance(given_property, GenericConnectionProperties)


class TCPUserTimeout(Enum):
    ADVERTISED_USER_TIMEOUT = 'tcp.user-timeout-value'
    USER_TIMEOUT_ENABLED = 'tcp.user-timeout'
    CHANGEABLE = 'tcp.user-timeout-recv'
