# coding=utf-8
# !/usr/bin/env python3

from preconnection import *
from endpoint import *
from transport_properties import *
from enumerations import *
import json

if __name__ == "__main__":
    ep = RemoteEndpoint()
    ep.with_address("127.0.0.1")
    ep.with_port(5000)

    tp = TransportProperties()
    print(tp.props)
    tp.require(SelectionProperties.ZERO_RTT_MSG)
    tp.prohibit(SelectionProperties.RELIABILIY)
    # tp.prefer(SelectionProperties.RELIABILIY)
    tp.ignore(SelectionProperties.CONGESTION_CONTROL)
    tp.ignore(SelectionProperties.PRESERVE_ORDER)
    tp.ignore(SelectionProperties.RETRANSMIT_NOTIFY)
    # tp.prefer(SelectionProperties.ZERO_RTT_MSG)

    preconnection = Preconnection(remote_endpoint=ep, transport_properties=tp)
    preconnection.initiate()





