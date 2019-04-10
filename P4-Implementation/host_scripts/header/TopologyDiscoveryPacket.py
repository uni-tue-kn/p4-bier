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
    def mysummary(self):
        return self.sprintf("identifier=%identifier%, dst_id=%dst_id%")




bind_layers(Ether, TopologyDiscovery, type=TYPE_TOPOLOGY_DISCOVERY)
