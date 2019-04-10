from scapy.all import *
import sys, os

TYPE_TOPOLOGY_DISCOVERY = 0xDD00
TYPE_IPV4 = 0x0800

class TopologyDiscovery(Packet):
    name = "TopologyDiscovery"
    fields_desc = [
        IntField("identifier", 0),
        XShortField("port", 0),
        IPField("ip", 0),
        MACField("mac", 0)

    ]

bind_layers(Ether, TopologyDiscovery, type=TYPE_TOPOLOGY_DISCOVERY)
