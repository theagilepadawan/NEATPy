from enum import Enum, auto

from utils import shim_print


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


class PreferenceLevel(Enum):
    """ An enumeration.
        Used when specifying a preference for :py:class:`selection_properties`.

        E.g an application specifying that a reliable transport is required would do this the following way::

            transport_properties.add(SelectionProperties.RELIABILITY, PreferenceLevel.REQUIRE)
    """
    REQUIRE = 2
    PREFER = 1
    IGNORE = 0
    AVOID = -1
    PROHIBIT = -2


class SelectionProperties(Enum):
    """
    An enumeration.
    Selection properties are used for application to specify applications requirements for transport
    and used for path and protocol stack selections. Selection properties are added to a :py:class:`transport_properties` object.
    """
    RELIABILITY = 'reliability' #: Default :py:class:`preference_level`.REQUIRE,
    PRESERVE_MSG_BOUNDARIES = 'preserve-msg-boundaries' #: Default :py:class:`preference_level`.PREFER,
    PER_MSG_RELIABILITY = 'per-msg-reliability' #: Default :py:class:`preference_level`.IGNORE,
    PRESERVE_ORDER = 'preserve-order' #: Default :py:class:`preference_level`.REQUIRE,
    ZERO_RTT_MSG = 'zero-rtt-msg' #: Default :py:class:`preference_level`.IGNORE,
    MULTISTREAMING = 'multistreaming' #: Default :py:class:`preference_level`.PREFER,
    PER_MSG_CHECKSUM_LEN_SEND = 'per-msg-checksum-len-send' #: Default :py:class:`preference_level`.IGNORE,
    PER_MSG_CHECKSUM_LEN_RECV = 'per-msg-checksum-len-recv' #: Default :py:class:`preference_level`.IGNORE,
    CONGESTION_CONTROL = 'congestion-control' #: Default :py:class:`preference_level`.REQUIRE,
    INTERFACE = 'interface' #: Default :py:class:`preference_level`
    PVD = 'pvd' #: Default :py:class:`preference_level`
    LOCAL_ADDRESS_PREFERENCE = 'local-address-preference' #: Default :py:class:`preference_level`
    MULTIPATH = 'multipath' #: Default :py:class:`preference_level`.PREFER
    DIRECTION = 'direction' #: Default :py:class:`communication_directions`
    RETRANSMIT_NOTIFY = 'retransmit-notify' #: Default :py:class:`preference_level`.IGNORE
    SOFT_ERROR_NOTIFY = 'soft-error-notify' #: Default :py:class:`preference_level`.IGNORE

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
            # SelectionProperties.INTERFACE: (),  # TODO: Settle on a reasoable default
            # SelectionProperties.PVD: (),  # TODO: Settle on a reasoable default
            # SelectionProperties.LOCAL_ADDRESS_PREFERENCE: AddressPreference.STABLE, # TODO: Need to dynamically set default (Listeners/Redezvous vs. others)
            SelectionProperties.MULTIPATH: PreferenceLevel.PREFER,
            SelectionProperties.DIRECTION: CommunicationDirections.BIDIRECTIONAL,
            SelectionProperties.RETRANSMIT_NOTIFY: PreferenceLevel.IGNORE,
            SelectionProperties.SOFT_ERROR_NOTIFY: PreferenceLevel.IGNORE
        }
        if prop:
            return defaults[prop]
        else:
            return defaults

    @staticmethod
    def set_property(given_props, prop, value):
        if not isinstance(value, PreferenceLevel):
            shim_print("Not a valid preference level provided - Aborting", level='error')
        else:
            given_props[prop] = value

