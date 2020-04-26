from enum import Enum, auto
from typing import Union

from colorama import Fore
from connection_properties import ConnectionProperties
from enumerations import SupportedProtocolStacks, ServiceLevel, PreferenceLevel
from message_properties import MessageProperties
from selection_properties import SelectionProperties
from utils import shim_print

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
    },

}


class TransportPropertyProfiles(Enum):
    """ Transport property profiles are used as a mechanism to pre-configure :py:class:`transport_properties` objects,
    with with frequently used sets of properties.
    """

    #: This profile provides reliable, in-order transport service with congestion control. An example of a protocol that provides this service is TCP.
    RELIABLE_INORDER_STREAM = auto()
    #: This profile provides message-preserving, reliable, in-order transport service with congestion control. An example of a protocol that provides this service is SCTP.
    RELIABLE_MESSAGE = auto()
    #: This profile provides unreliable datagram transport service. An example of a protocol that provides this service is UDP.
    UNRELIABLE_DATAGRAM = auto()


class TransportProperties:

    def __init__(self, property_profile: TransportPropertyProfiles = None):
        """ Transport properties is the collection of :py:class:`message_properties`, :py:class:`selection_properties`
        and :py:class:`connection_properties`.

        :param property_profile: Transport property profile to use
        """
        self.selection_properties = SelectionProperties.get_default()
        self.message_properties = MessageProperties.get_default()
        self.connection_properties = ConnectionProperties.get_default()

        # Updates the selection properties dict with values from the transport profile
        if property_profile:
            if property_profile is TransportPropertyProfiles.RELIABLE_INORDER_STREAM:
                self.selection_properties.update(
                    {SelectionProperties.RELIABILITY: PreferenceLevel.REQUIRE,
                     SelectionProperties.PRESERVE_ORDER: PreferenceLevel.REQUIRE,
                     SelectionProperties.CONGESTION_CONTROL: PreferenceLevel.REQUIRE,
                     SelectionProperties.PRESERVE_MSG_BOUNDARIES: PreferenceLevel.PROHIBIT
                     })
            elif property_profile is TransportPropertyProfiles.RELIABLE_MESSAGE:
                self.selection_properties.update({
                    SelectionProperties.RELIABILITY: PreferenceLevel.REQUIRE,
                    SelectionProperties.PRESERVE_ORDER: PreferenceLevel.REQUIRE,
                    SelectionProperties.CONGESTION_CONTROL: PreferenceLevel.REQUIRE,
                    SelectionProperties.PRESERVE_MSG_BOUNDARIES: PreferenceLevel.REQUIRE
                })
            elif property_profile is TransportPropertyProfiles.UNRELIABLE_DATAGRAM:
                self.selection_properties.update({
                    SelectionProperties.RELIABILITY: PreferenceLevel.PROHIBIT,
                    SelectionProperties.PRESERVE_ORDER: PreferenceLevel.IGNORE,
                    SelectionProperties.CONGESTION_CONTROL: PreferenceLevel.IGNORE,
                    SelectionProperties.PRESERVE_MSG_BOUNDARIES: PreferenceLevel.REQUIRE})
                self.message_properties.update({MessageProperties.IDEMPOTENT: True})

    def __filter_protocols(self, protocol_level, preference_level, candidates):
        remove_list = []
        for prop, preference in self.selection_properties.items():
            if preference == preference_level:
                for protocol in candidates:
                    if protocols_services[protocol][prop] == protocol_level:
                        if protocol not in remove_list:
                            shim_print(f'{protocol.name} is removed as it does not satisfy {prop.name} requirements')
                        remove_list.append(protocol)
        return [protocol for protocol in candidates if protocol not in remove_list]

    def add(self, prop: Union[SelectionProperties, MessageProperties, ConnectionProperties], value):
        """ Add a property to the transport property object.

        :param prop: Property to add
        :param value: Value for given property
        """
        if isinstance(prop, SelectionProperties):
            shim_print("Setting selection property...")
            SelectionProperties.set_property(self.selection_properties, prop, value)
        elif isinstance(prop, ConnectionProperties):
            shim_print("Setting connection property...")
            ConnectionProperties.set_property(self.connection_properties, prop, value)
        elif isinstance(prop, MessageProperties):
            MessageProperties.set_property(self.message_properties, prop, value)
        else:
            shim_print("No valid property given - ignoring", level='error')

    def avoid(self, prop: SelectionProperties):
        """ Set the preference level to avoid for the passed selection property.

        :param prop: Selection property to set ``avoid`` as preference level for.
        """
        if not isinstance(prop, SelectionProperties):
            shim_print("Property given is not a selection property - ignoring", level='error')
        else:
            self.add(prop, PreferenceLevel.AVOID)

    def require(self, prop: SelectionProperties):
        """Set the preference level to require for the passed selection property.

        :param prop: Selection property to set ``require`` as preference level for.
        """
        if not isinstance(prop, SelectionProperties):
            shim_print("Property given is not a selection property - ignoring", level='error')
        else:
            self.add(prop, PreferenceLevel.REQUIRE)

    def prefer(self, prop: SelectionProperties):
        """ Set the preference level to prefer for the passed selection property.

        :param prop: Selection property to set ``prefer`` as preference level for.
        """
        if not isinstance(prop, SelectionProperties):
            shim_print("Property given is not a selection property - ignoring", level='error')
        else:
            self.add(prop, PreferenceLevel.PREFER)

    def ignore(self, prop: SelectionProperties):
        """  Set the preference level to ignore for the passed selection property.

        :param prop: Selection property to set ``ignore`` as preference level for.
        """
        if not isinstance(prop, SelectionProperties):
            shim_print("Property given is not a selection property - ignoring", level='error')
        else:
            self.add(prop, PreferenceLevel.IGNORE)

    def prohibit(self, prop: SelectionProperties):
        """  Set the preference level to prohibit for the passed selection property.

        :param prop: Selection property to set ``prohibit`` as preference level for.
        """
        if not isinstance(prop, SelectionProperties):
            shim_print("Property given is not a selection property - ignoring", level='error')
        else:
            self.add(prop, PreferenceLevel.PROHIBIT)

    def default(self, prop: SelectionProperties):
        """ Set the default preference level for the given selection property.

        :param prop: Selection property to reset to default preference level for.
        """
        if not isinstance(prop, SelectionProperties):
            shim_print("Property given is not a selection property - ignoring", level='error')
        else:
            self.add(prop, SelectionProperties.get_default(prop))

    def select_protocol_stacks_with_selection_properties(self):
        properties = None
        candidates = SupportedProtocolStacks.get_protocol_stacks_on_system()

        # If idempotent property is not set, UDP is not a valid candidate
        if not self.message_properties[MessageProperties.IDEMPOTENT]:
            shim_print("UDP is removed as message property Idempotent is not true")
            candidates.remove(SupportedProtocolStacks.UDP)

        # "Internally, the transport system will first exclude all protocols and paths that match a Prohibit..."
        candidates = self.__filter_protocols(ServiceLevel.INTRINSIC_SERVICE, PreferenceLevel.PROHIBIT, candidates)

        # "...then exclude all protocols and paths that do not match a Require"
        candidates = self.__filter_protocols(ServiceLevel.NOT_PROVIDED, PreferenceLevel.REQUIRE, candidates)

        if not candidates:
            return None

        # "...then sort candidates according to Preferred properties" [Cite]
        elif len(candidates) > 1:
            ranking_dict = dict(zip(candidates, [0] * len(candidates)))

            for prop, preference in self.selection_properties.items():
                if preference.value == PreferenceLevel.PREFER.value:
                    for protocol in candidates:
                        if protocols_services[protocol][prop].value >= ServiceLevel.OPTIONAL.value:
                            shim_print(f'{protocol.name} supports {prop.name}')
                            ranking_dict[protocol] += 1
            ranking = sorted(ranking_dict.items(), key=lambda f: f[1], reverse=True)
            ranking_string = Fore.BLUE + f'{Fore.RESET} --> {Fore.BLUE}'.join(map(lambda x: str(x[0].name), ranking))
            shim_print(f"Ranking after filtering: {ranking_string}")
            candidates = [item[0] for item in ranking]

        if SupportedProtocolStacks.TCP.name in candidates and self.selection_properties[
            SelectionProperties.MULTIPATH] and self.selection_properties[
            SelectionProperties.MULTIPATH].value != PreferenceLevel.PROHIBIT.value:
            if SupportedProtocolStacks.check_for_mptcp():
                candidates.append(SupportedProtocolStacks.MPTCP)
                shim_print("MPTCP enabled on system")
        return candidates




def test():
    tp = TransportProperties()
    tp.add(SelectionProperties.RELIABILITY, PreferenceLevel.REQUIRE)
    tp.prohibit(SelectionProperties.PRESERVE_MSG_BOUNDARIES)

