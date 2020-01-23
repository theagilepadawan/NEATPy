from enum import Enum, auto
from enumerations import *


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
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_CONCURRENT_WITH_CONNECTION_ESTABLISHMENT: -1, # TODO: Settle for default.
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_BEFORE_FRAGMENTATION_OR_SEGMENTATION: -1, # TODO: Settle for default.
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_SEND: -1, # TODO: Settle for default.
            ConnectionProperties.MAXIMUM_MESSAGE_SIZE_ON_RECEIVE: -1, # TODO: Settle for default.
            ConnectionProperties.CAPACITY_PROFILE: CapacityProfiles.DEFAULT,
            ConnectionProperties.BOUNDS_ON_SEND_OR_RECEIVE_RATE: (-1, -1),
            ConnectionProperties.USER_TIMEOUT_TCP: (None, None, None)
        }

        if prop:
            return defaults[prop]
        else:
            return defaults
