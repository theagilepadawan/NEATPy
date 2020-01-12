from enumerations import *
from utils import *
from colorama import Fore, Back, Style
import json

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
        # SelectionPropertiesDefaults.DIRECTION: ,
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
        # SelectionPropertiesDefaults.DIRECTION: ,
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
        # SelectionPropertiesDefaults.DIRECTION: ,
        SelectionProperties.RETRANSMIT_NOTIFY: ServiceLevel.NOT_PROVIDED,
        SelectionProperties.SOFT_ERROR_NOTIFY: ServiceLevel.INTRINSIC_SERVICE,
    },
}


class TransportProperties:

    def __init__(self):
        self.props = {prop: SelectionProperties.get_default(prop) for name, prop in
                      SelectionProperties.__members__.items()}

    def add(self, prop: SelectionProperties, preference: PreferenceLevel):
        self.props[prop] = preference

    def require(self, prop: SelectionProperties):
        self.props[prop] = PreferenceLevel.REQUIRE

    def prefer(self, prop: SelectionProperties):
        self.props[prop] = PreferenceLevel.PREFER

    def ignore(self, prop: SelectionProperties):
        self.props[prop] = PreferenceLevel.IGNORE

    def avoid(self, prop: SelectionProperties):
        self.props[prop] = PreferenceLevel.AVOID

    def prohibit(self, prop: SelectionProperties):
        self.props[prop] = PreferenceLevel.PROHIBIT

    def default(self, prop: SelectionProperties):
        self.props[prop] = PreferenceLevel.REQUIRE

    def filter_protocols(self, protocol_level, preference_level, candidates):
        remove_list = []
        props_with_preference_level = filter((lambda p: self.props[p] == preference_level), self.props)
        valid_candidates_after_filtering = filter((lambda c: True), candidates)

        ########

        remove_list = []
        for prop, preference in self.props.items():
            if preference == preference_level:
                for protocol in candidates:
                    if protocols_services[protocol][prop] == protocol_level:
                        if protocol not in remove_list:
                            shim_print(f'{protocol.value} is removed as it does not satisfy {prop.name} requirements')
                        remove_list.append(protocol)
        return [protocol for protocol in candidates if protocol not in remove_list]

    def to_json(self):
        properties = None
        candidates = [SupportedProtocolStacks.TCP, SupportedProtocolStacks.UDP, SupportedProtocolStacks.SCTP]

        # "Internally, the transport system will first exclude all protocols and paths that match a Prohibit..."
        candidates = self.filter_protocols(ServiceLevel.INTRINSIC_SERVICE, PreferenceLevel.PROHIBIT, candidates)

        # "...then exclude all protocols and paths that do not match a Require"
        candidates = self.filter_protocols(ServiceLevel.NOT_PROVIDED, PreferenceLevel.REQUIRE, candidates)
        if len(candidates) == 1:
            properties = json.dumps({"transport": {"value": candidates.pop(0).value, "precedence": 1}})

        # "...then sort candidates according to Preferred properties" [Cite]
        elif len(candidates) > 1:
            ranking_dict = dict(zip(candidates, [0] * len(candidates)))
            for prop, preference in self.props.items():
                if preference.value == PreferenceLevel.PREFER.value:
                    for protocol in candidates:
                        if protocols_services[protocol][prop].value >= ServiceLevel.OPTIONAL.value:
                            shim_print(f'{protocol.value} supports {prop.name}')
                            ranking_dict[protocol] += 1
            ranking = sorted(ranking_dict.items(), key=lambda f: f[1], reverse=True)
            ranking_string = Fore.BLUE + f'{Fore.RESET} --> {Fore.BLUE}'.join(map(lambda x: str(x[0].value), ranking))
            shim_print(f"Ranking after filtering: {ranking_string}")
            candidates = [item[0].value for item in ranking]
            properties = json.dumps({"transport": {"value": candidates, "precedence": 2}})
        else:
            properties = None

        return properties
