from utils import *
from colorama import Fore, Back, Style
import json
from selection_properties import *
from message_context import *
from enum import Enum, auto
from enumerations import *
from connection_properties import *

protocols_services = {
    SupportedProtocolStacks.TCP: {
        SelectionProperties.RELIABILITY: ServiceLevel.INTRINSIC_SERVICE,
        SelectionProperties.PRESERVE_MSG_BOUNDARIES: ServiceLevel.NOT_PROVIDED,
        SelectionProperties.PER_MSG_RELIABILITY: ServiceLevel.NOT_PROVIDED,
        SelectionProperties.PRESERVE_ORDER: ServiceLevel.INTRINSIC_SERVICE,
        SelectionProperties.ZERO_RTT_MSG: ServiceLevel.OPTIONAL,
        SelectionProperties.MULTISTREAMING: ServiceLevel.OPTIONAL,
        SelectionProperties.PER_MSG_CHECKSUM_LEN_SEND: ServiceLevel.NOT_PROVIDED,
        SelectionProperties.PER_MSG_CHECKSUM_LEN_RECV: ServiceLevel.NOT_PROVIDED,
        SelectionProperties.CONGESTION_CONTROL: ServiceLevel.INTRINSIC_SERVICE,
        SelectionProperties.MULTIPATH: ServiceLevel.OPTIONAL,
        SelectionProperties.DIRECTION: ServiceLevel.INTRINSIC_SERVICE,
        SelectionProperties.RETRANSMIT_NOTIFY: ServiceLevel.INTRINSIC_SERVICE,
        SelectionProperties.SOFT_ERROR_NOTIFY: ServiceLevel.INTRINSIC_SERVICE,
    },

    SupportedProtocolStacks.SCTP: {
        SelectionProperties.RELIABILITY: ServiceLevel.OPTIONAL,
        SelectionProperties.PRESERVE_MSG_BOUNDARIES: ServiceLevel.INTRINSIC_SERVICE,
        SelectionProperties.PER_MSG_RELIABILITY: ServiceLevel.INTRINSIC_SERVICE,
        SelectionProperties.PRESERVE_ORDER: ServiceLevel.INTRINSIC_SERVICE,
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
    RELIABLE_INORDER_STREAM = {SelectionProperties.RELIABILITY: PreferenceLevel.REQUIRE,
                               SelectionProperties.PRESERVE_ORDER: PreferenceLevel.REQUIRE,
                               SelectionProperties.CONGESTION_CONTROL: PreferenceLevel.REQUIRE,
                               SelectionProperties.PRESERVE_MSG_BOUNDARIES: PreferenceLevel.IGNORE}

    RELIABLE_MESSAGE = {SelectionProperties.RELIABILITY: PreferenceLevel.REQUIRE,
                        SelectionProperties.PRESERVE_ORDER: PreferenceLevel.REQUIRE,
                        SelectionProperties.CONGESTION_CONTROL: PreferenceLevel.REQUIRE,
                        SelectionProperties.PRESERVE_MSG_BOUNDARIES: PreferenceLevel.REQUIRE}

    UNRELIABLE_DATAGRAM = {SelectionProperties.RELIABILITY: PreferenceLevel.IGNORE,
                           SelectionProperties.PRESERVE_ORDER: PreferenceLevel.IGNORE,
                           SelectionProperties.CONGESTION_CONTROL: PreferenceLevel.IGNORE,
                           SelectionProperties.PRESERVE_MSG_BOUNDARIES: PreferenceLevel.REQUIRE}
    # Todo: Final layout of transport, selection and messageproperties
    # MessageContextProperties.IDEMPOTENT: True}


class TransportProperties:

    def __init__(self, property_profile=None):
        self.selection_properties = SelectionProperties.get_default()
        self.message_properties = MessageProperties.get_default()
        self.connection_properties = ConnectionProperties.get_default()

        # Updates the selection properties dict with values from the transport profile
        if property_profile:
            self.selection_properties.update(property_profile.value)
            #self.selection_properties = property_profile.value


    def filter_protocols(self, protocol_level, preference_level, candidates):
        remove_list = []
        for prop, preference in self.selection_properties.items():
            if preference == preference_level:
                for protocol in candidates:
                    if protocols_services[protocol][prop] == protocol_level:
                        if protocol not in remove_list:
                            shim_print(f'{protocol.name} is removed as it does not satisfy {prop.name} requirements')
                        remove_list.append(protocol)
        return [protocol for protocol in candidates if protocol not in remove_list]

    def to_json(self):
        properties = None
        candidates = SupportedProtocolStacks.get_protocol_stacks_on_system()

        # "Internally, the transport system will first exclude all protocols and paths that match a Prohibit..."
        candidates = self.filter_protocols(ServiceLevel.INTRINSIC_SERVICE, PreferenceLevel.PROHIBIT, candidates)

        # "...then exclude all protocols and paths that do not match a Require"
        candidates = self.filter_protocols(ServiceLevel.NOT_PROVIDED, PreferenceLevel.REQUIRE, candidates)
        if len(candidates) == 1:
            properties = json.dumps({"transport": {"value": candidates.pop(0).name, "precedence": 1}})

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
            candidates = [item[0].name for item in ranking]

            if SupportedProtocolStacks.TCP.name in candidates and self.selection_properties[SelectionProperties.MULTIPATH] and self.selection_properties[SelectionProperties.MULTIPATH].value >= PreferenceLevel.IGNORE.value:
                if SupportedProtocolStacks.check_for_mptcp():
                    candidates.append(SupportedProtocolStacks.MPTCP.name)
                    shim_print("MPTCP enabled on system")

            properties = json.dumps({"transport": {"value": candidates, "precedence": 2}})

            # properties = json.dumps({"transport": {"value": candidates, "precedence": 2},
            #                          "SO/SOL_SOCKET/TCP_NODELAY": {"value": 1, "precedence": 1}})

        else:
            properties = None

        return properties
